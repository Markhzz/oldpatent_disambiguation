/*finalize*/

global dropbox "C:\Users\Liulihua\Dropbox\PatentAssigneeMatching\"
global data "$dropbox\patents_data_eb\code\assignee_clustering\exp_out"

* 1. w/ constraint
insheet using "$data\disambiguation.tsv",clear
ren v1 assigneeid
ren v2 entityid

gen patentid = substr(assigneeid,1,9)
replace assigneeid = substr(assigneeid,11,46)
preserve
	import excel using "$data\assign_rev_v4.xlsx",firstrow clear
	ren assign assignee
	keep assigne uuid
	ren uuid assigneeid
	tempfile assignee
	save `assignee',replace
restore

merge 1:1 assigneeid using `assignee'
assert _m == 3
drop _m
bys entityid: gen num_assignee = _N
sum num_assignee,d
tab num_assignee
so num_assignee entityid assigneeid

save "$data\disambiguation_wrule.dta",replace

* 2. w/o constraint
insheet using "$data\disambiguation_noconstraint.tsv",clear
ren v1 assigneeid
ren v2 entityid

gen patentid = substr(assigneeid,1,9)
replace assigneeid = substr(assigneeid,11,46)
preserve
	import excel using "$data\assign_rev_v4.xlsx",firstrow clear
	ren assign assignee
	keep assigne uuid
	ren uuid assigneeid
	tempfile assignee
	save `assignee',replace
restore

merge 1:1 assigneeid using `assignee'
assert _m == 3
drop _m
bys entityid: gen num_assignee = _N
sum num_assignee,d
tab num_assignee
so num_assignee entityid assigneeid

save "$data\disambiguation_worule.dta",replace


* 2. w/o constraint, self-made vectorizer
insheet using "$data\disambiguation_norule_selfvect.tsv",clear
ren v1 assigneeid
ren v2 entityid

gen patentid = substr(assigneeid,1,9)
replace assigneeid = substr(assigneeid,11,46)
preserve
	import excel using "$data\assign_rev_v4.xlsx",firstrow clear
	ren assign assignee
	keep assigne uuid
	ren uuid assigneeid
	tempfile assignee
	save `assignee',replace
restore

merge 1:1 assigneeid using `assignee'
assert _m == 3
drop _m
bys entityid: gen num_assignee = _N
sum num_assignee,d
tab num_assignee
so num_assignee entityid assigneeid

save "$data\disambiguation_norule_selfvect.dta",replace

* evaluate the differences
u "$data\disambiguation_wrule.dta",clear
ren entityid entityid1
merge 1:1 assigneeid using "$data\disambiguation_worule.dta"
assert _m == 3
drop _m

bys entityid1: gen norule_id = entityid[1]
count if entityid != norule_id
* w/in group created w/ rules, all records are in the same group created w/o rules

bys entityid: gen rule_id = entityid1[1]
count if entityid1 != rule_id
* 50 records are reclassified w/ rules
gen keep_ = 1 if entityid1 != rule_id
bys entityid: egen keep = max(keep_)
preserve
	keep if keep == 1
	order keep_ entityid entityid1 assignee 
	save "$data\diff_rule.dta",replace
restore

u "$data\disambiguation_worule.dta",clear
ren entityid entityid1
merge 1:1 assigneeid using "$data\disambiguation_norule_selfvect.dta"
assert _m == 3
drop _m

bys entityid1: gen selfvectid = entityid[1]
count if entityid != selfvectid
* 36 records are reclassified if using assignee vectorizer
preserve
	gen keep_ = 1 if entityid != selfvectid
	bys entityid1: egen keep = max(keep_)
	keep if keep == 1
	so entityid1 entityid
	order keep_ entityid entityid1 assignee
	save "$data\diff_vector1.dta",replace
restore

* w/in group created w/ rules, all records are in the same group created w/o rules

bys entityid: gen rule_id = entityid1[1]
count if entityid1 != rule_id
* 50 records are reclassified w/ rules
preserve
	gen keep_ = 1 if entityid1 != rule_id
	bys entityid: egen keep = max(keep_)
	keep if keep == 1
	so entityid entityid1
	order keep_ entityid entityid1 assignee 
	save "$data\diff_vector2.dta",replace
restore
