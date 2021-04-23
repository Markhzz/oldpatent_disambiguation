# oldpatent_disambiguation
This program is used to parse and disambiguate the extracted assignees for old patents. The codes are revsied versions of the work by Nicholas Monath and Sarvothaman Madhavan:https://github.com/PatentsView/PatentsView-Disambiguation/. I made several modifications:
1) only calculate the distance of the name string, rather than the distance of name and location;
2) add the code for parsing and extracting the assignee from raw text in the code: \pv\disambiguation\assignee\build_assignee.py

## Setup

```
pip install git+git://github.com/iesl/grinch.git
conda install pytorch==1.2.0 torchvision==0.4.0 cudatoolkit=9.2 -c pytorch
```
Also, please download the files in this link and save them under the folder: resources
https://www.dropbox.com/sh/zgyi1kkyjikk60c/AAD2Yjg9ovdZVu96IKmeOSOga?dl=0

e.g.
/resources/permid_entity_info.pkl
/resources/permid_vectorizer.pkl


## 1. Duplication of Patentsview (sample size 10,000)

The raw data set has 6,980,559 patent - assignee combination. I randomly extract 10,000 (0.14% of total) observations and create a random sample. I apply the algorithm on this random sample and compare the clustering output (assignee_id_rep) to the one created by Patentsview (assignee_id). Among these 10,000 observations, 53 records are clustered differently.

### Build Mentions & Canopies

```
python -m pv.disambiguation.assignee.build_assignee_name_mentions_sql
```

### Run clustering

```
python -m pv.disambiguation.assignee.run_clustering_duplicate
```

### Finalize

```
python -m pv.disambiguation.assignee.finalize_duplicate
# use stata
# please revise the path in the line 3: global dropbox "C:\Users\Liulihua\Dropbox\PatentAssigneeMatching\"
duplication.do is used to load the output and compare it to the original data set, where assignee_id is the entity id created by Patentsview, and assignee_id_rep is the id that I duplicated.
```

### Difference

```
The replication leads to a larger group, where the replication program separate 50 records from their entity group. E.g:

assignee
Commissariat a l'Energie Atomique
Commissariat a l'Energie Atomique
Commissariat à l'énergie atomique et aux énergies alternatives
Commissariat a l'Energie Atomique
Commissariat a l'Energie Atomique et Aux Energies Alternatives
Commissariat a l'energie Atomique
COMMISSARIAT A L'ENERGIE ATOMIQUE ET AUX ENERGIES ALTERNATIVES

SEB
SEB S.A.

Boehringer Ingelheim International GbmH
Boehringer Ingelheim International GmbH
Boehringer Ingelheim International GmbH
Boehringer Ingelheim Pharma GmbH & Co KG

SHENZHEN CHINA STAR OPTOELECTRONICS SEMICONDUCTOR DISPLAY TECHNOLOGY CO., LTD.
Wuhan China Star Optoelectronics Semiconductor Display Technology Co., Ltd.

```





## 2. Assignee Disambiguation w/ PermID vectorizer and PermID entity rules

I use the PermID database to create the vectorizer, which is used to convert the document into matrices and assign TF-IDF weights. Also, I use the PermID database to make a rule, where two records w/ different PermID can't be clustered into one group.

### Build Mentions & Canopies

Please change the path to the corresponding folder in your dropbox (line 54,55 in pv/disambiguation/assignee/build_assignee.py
flags.DEFINE_string('path', 'C:/Users/Liulihua/Dropbox/PatentAssigneeMatching/patents_data_eb/text/', '')
flags.DEFINE_string('project', 'C:/Users/Liulihua/Dropbox/PatentAssigneeMatching/', '')
```
python -m pv.disambiguation.assignee.build_assignee
# need to revise the line 54 & 55 to your project path
```

### Run clustering

```
python -m pv.disambiguation.assignee.run_clustering
```

### Finalize

```
python -m pv.disambiguation.assignee.finalize
# use stata
# Please revise the line 3 to your dropbox folder global dropbox "C:\Users\Liulihua\Dropbox\PatentAssigneeMatching\"
finalize.do (line 1-30)
```





## 3. Assignee Disambiguation w/ PermID vectorizer w/o PermID entity rules

Here I exclude the usage of PermID as a must_not_link rule

### Build Mentions & Canopies

Please change the path to the corresponding folder in your dropbox (line 54,55 in pv/disambiguation/assignee/build_assignee.py
flags.DEFINE_string('path', 'C:/Users/Liulihua/Dropbox/PatentAssigneeMatching/patents_data_eb/text/', '')
flags.DEFINE_string('project', 'C:/Users/Liulihua/Dropbox/PatentAssigneeMatching/', '')
```
python -m pv.disambiguation.assignee.build_assignee
# need to revise the line 54 & 55 to your project path
```

### Run clustering

```
python -m pv.disambiguation.assignee.run_clustering_noconstraint
```

### Finalize

```
python -m pv.disambiguation.assignee.finalize_noconstraint
# use stata
finalize.do (line 31-56)
```





## 4. Assignee Disambiguation w/ raw assignee vectorizer w/o PermID entity rules

Here I exclude the usage of PermID as a must_not_link rule

### Build Mentions & Canopies
Please change the path to the corresponding folder in your dropbox (line 54,55 in pv/disambiguation/assignee/build_assignee.py
flags.DEFINE_string('path', 'C:/Users/Liulihua/Dropbox/PatentAssigneeMatching/patents_data_eb/text/', '')
flags.DEFINE_string('project', 'C:/Users/Liulihua/Dropbox/PatentAssigneeMatching/', '')
```
python -m pv.disambiguation.assignee.build_assignee
# need to revise the line 54 & 55 to your project path
```

### Run clustering

```
python -m pv.disambiguation.assignee.run_clustering_norule_selfvect
```

### Finalize

```
python -m pv.disambiguation.assignee.finalize_norule_selfvect
# use stata
finalize.do (line 56-end)
```



## Comparing different methods

### 2. w/ rules + PermID TF-IDF vectorizer VS 3. w/o rules + PermID TF-IDF vectorizer 

```
1) The output of 2. is finer than the output of 3. 
2) 50 records are classified into a finer group when using the method 2.

assignees that are clustered into one group under method 3 but are separated under method 2: \patents_data_eb\code\assignee_clustering\exp_out\diff_rule.dta

WILLIAM E. HILL
WILLIAM JOHN HILL.

THE CUTLER-HAMMER MEG. 00.
THE CUTLER-HAMMER MEG. CO.

ERICE-CAMPBELL COTTON PICKER CORPORATION
PRICE-■ CAMPBELL COTTON PICKER CORPORATION
PRICE-CAMPBELL COTTON PICKER CORPORATION
PRICE-CAMPBELL COTTON PICKER CORPORATION
PRICE-CAMPBELL COTTON PICKER CORPORATION

CONTINENTAL GIN COMPANY
CONTINENTAL PAPER BAG COMPANY

THE SAFETY CAR HEATING & LIGHTING COMPANY
SAFETY CAR HEATING AND LIGHTING COMPANY
SAFETY CAR HEATING AND LIGHTING COMPANY
SAFETY CAR HEATING AND LIGHTING COMPANY
SAFETY CAR HEATING & LIGHTING COMPANY
SAFETY CAE HEATING AND LIGHTING COMPANY
```



### 3. w/o rules + PermID TF-IDF vectorizer VS 4. w/o rules + raw assignee TF-IDF vectorizer

```
1) Sometimes, output of method 3 is finer, and somtimes the other way around.
2) 36 records are classified into a finer group when using the method 4.

assignees that are clustered into one group under method 3 but are separated under method 4:\patents_data_eb\code\assignee_clustering\exp_out\diff_vector1.dta

TROY LAUNDRY MACHINERY COMPANY
TROY LAUNDRY MACHINERY COMPANY
TROY LAUNDRY MACHINERY COMPANY
TROY LAUNDRY MACHINERY COMPANY
^AMERICAN LAUNDRY MACHINERY COMPANY
TROT LAUNDRY MACHINERY COMPANY
THE NATIONAL LAUNDRY MACHINERY COMPANY

MOORE ELECTRICAL dp.
MOORE ELECTRICAL COMPANY
MOORE ELECTRICAL COMPANY

SELLERS MANUFACTURING COMPANY
SELLERS MANUFACTURING COMPANY
SELLERS MANUFACTURING COMP ANT

AMERICAN BUTTON COMPANY
GERMAN-AMERICAN BUTTON COMPANY

3) 2 records are classified into a finer group when using method 3.

assignees that are clustered into one group under method 4 but are separated under method 3:\patents_data_eb\code\assignee_clustering\exp_out\diff_vector2.dta

SOCIETE ANONYME POUR . Ii’EXPIiOITATION DES PROCEDES WESTINGHOUSE-LEBEANC
SOCIETE ANONYME POUR L’EXPLOITATION DES PROCEDES WESTINGHOUSE-LEBLANC

NATIONAL GAS LIGHT COMPANY
GENERAL GAS LIGHT COMPANY

```





