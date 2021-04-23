/* replication */

global dropbox "C:\Users\Liulihua\Dropbox\PatentAssigneeMatching\"
global data "$dropbox\patents_data_eb\code\assignee_clustering\exp_out"

/*
insheet using "$data\patentsview\rawassignee\rawassignee.tsv",clear
sample 10000,count
export excel using "$data\replication\rawassignee_sample.xlsx",firstrow(variables) replace
*/

insheet using "$data\disambiguation_duplicate.tsv",clear
ren v1 mention_id
ren v2 assignee_id_rep
split mention_id,p("-")
ren mention_id1 patent_id
keep patent_id assignee_id_rep

preserve
	import excel using "$dropbox\patents_data_eb\code\assignee_clustering\resources\rawassignee_sample.xlsx",firstrow clear
	tempfile sample
	save `sample',replace
restore

merge 1:1 patent_id using `sample'
assert _m == 3
drop _m

bys assignee_id: gen first_assignee_rep = assignee_id_rep[1]
gen check_ = 1 if first_assignee_rep!=assignee_id_rep
bys assignee_id: egen check = max(check_)

preserve
	keep if check == 1
	order check_ assignee_id assignee_id_rep first_assignee_rep organization
	save "$data\replication_diff.dta",replace
	* replication fails to fully duplicate the assignee_id, where among 10000, there are 53 observation that is clustered differently;
restore

bys assignee_id_rep: gen first_assignee = assignee_id[1]
gen check2_ = 1 if first_assignee!=assignee_id
bys assignee_id: egen check2 = max(check2_)

preserve
	keep if check2 == 1
	order check2_ assignee_id_rep assignee_id first_assignee organization
	assert check2_ == 1 if mi(organization)
	* all sort of misclustered are due to missing of assignee name;
restore
