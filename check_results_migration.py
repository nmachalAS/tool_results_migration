import os
import json
import sys
from collections import OrderedDict
"""
Check the results from immigration from allure-results.json files. 
Take as input the repository that contains all allure-results folders.
The allure-results folders need to be in the same directory. 
The name of all allure-results folders need to contains "allure-results".
Example of names :
    -"allure-results_1" : directory for results for batch 1
    -"allure-results_2" : directory for results for batch 2
    .......


There is 1 folder as output named Results_Jobs that contains 6 files :
    -Results_Job/global report of errors.txt is a file that reports the numbers and kinds of errors that occured.
    -Results_Job/context_missing_with_users.txt identify all missing contexts matching with the users.
    -Results_Job/unique_context_missing.txt lists all unique missing contexts
    -Results_Job/length_element_bigger.txt reports users with failed error : Schema validation error\n[Error] Element length must be lower or equal to 50!
    -Results_Job/user_missing.txt reports users with failed error : User doesnt exist.
    -Results_Job/others_errors.txt reports all others issues matching with the users.

usage: python check_results_migration.py <folder with all allure_results directory>

"""


def listAllAllureResultsFolder(path_allure_results):
    if path_allure_results[-1]!="/":
        path_allure_results+="/"
    list_allure_results_folders = [path_allure_results+ f+"/" for f in os.listdir(path_allure_results) if (os.path.isdir(path_allure_results+ f) and "allure-results" in f)]
    return list_allure_results_folders

def createFolderForCheckingResults():
    path_to_past_results="Results_Job/"
    try:
        os.mkdir(path_to_past_results)
    except OSError:
        print ("Creation of the directory %s failed, it probably already exists." % path_to_past_results)
    else:
        print ("Successfully created the directory Results_Job for results %s " % path_to_past_results)
    return path_to_past_results
    

def treatRolesDifferent(message,user_id,roles_differents,dict_context_roles_users,admin_roles):
    roles_differents.append(user_id)
                    
    all_contexts_changes=message.split("Roles are different")[1:]
    for context_changed in all_contexts_changes:
        admin_roles.append(user_id)
        list_added=[]
        list_removed=[]
        context=context_changed.split("in ")[1].split(" New")[0]
        if context not in dict_context_roles_users.keys():
            dict_context_roles_users[context]={}

        new_old=context_changed.split("Old",1)

        new=new_old[0].split("New ")[1][2:-3]
        old=new_old[1].split("\n",1)[0].replace(" ", "")[1:-1]
        list_new=new.split(",")
        list_old=old.split(",")
        for new in list_new:
            try:
                list_new[list_new.index(new)]=int(new)
            except:
                list_new=[]
        for old in list_old:
            try:
                list_old[list_old.index(old)]=int(old)
            except:
                list_old=[]
        for new in list_new:
            if new not in list_old:
                list_added.append(new)
        for old in list_old:
            if old not in list_new:
                list_removed.append(old)
        difference={}
        difference="added : " + str(list_added)+ " ; removed : "+str(list_removed)
        if difference not in dict_context_roles_users[context].keys():
            dict_context_roles_users[context][difference]={}
            dict_context_roles_users[context][difference]["number of users with this context with this difference : "]=1
        else:
            dict_context_roles_users[context][difference]["number of users with this context with this difference : "]+=1

    return roles_differents,dict_context_roles_users,admin_roles

def treatOrgaContextChanged(orga_context_added,orga_context_removed,message,user_id):

    all_contexts_changed=message.split("Organizational Context")[1:]
    for context_changed in all_contexts_changed:
        action=context_changed.split("[")[0].replace(" ","")
        context=context_changed.split("[")[1].split("]",1)[0]
        if action=="added":
            if context not in orga_context_added.keys():
                orga_context_added[context]=1
            else:
                orga_context_added[context]+=1
        if action=="removed":
            if context not in orga_context_removed.keys():
                orga_context_removed[context]=1
            else:
                orga_context_removed[context]+=1

        
    return orga_context_added, orga_context_removed

def getIdFromJson(data):
    name=data["name"]
    if 'UserFileDifference_test' in name :
        id=name.split("| ",1)[1].split("]",1)[0]
    elif 'ThirdPartyOrgsFileDifference_test' in name:
        id=name.split("[",1)[1].split("]",1)[0]
    elif 'UserMigration_test' in name:
        id=data["steps"][0]["name"].split("[",1)[1].split(",",1)[0]
    elif 'ThirdPartyOrg_test' in name:
        id=data["steps"][0]["name"].split(": ",1)[1]
    else:
        id=name
    return id

def IsKnownUserDiffError(message):
    if ("Organizational Context added" in message or "Organizational Context removed" in message 
        or "Communication Channel" in message or "First Name is incorrect" in message or "Last Name is incorrect" in message
        or "Roles are different" in message):
        return True
    else:
        return False

def isKnownError(message):
    listError=["User does not exist","Schema validation error\n[Error] Element length must be lower or equal to 50!",
        "[USER DIFFERENCES]","Context","[NEW USER]","[REMOVED USER]","[NEW ORGANIZATION]","[REMOVED ORGANIZATION]"]
    for error in listError:
        if error in message:
            return True
    else:
        return False

def treat_json_file_results(json_file,dictMapErrors,total_of_failures_missing_context,countfailed):
    dict_context_missing=dictMapErrors["dict_context_missing"]
    missing_users=dictMapErrors["missing_users"]
    length_name_bigger_fifty=dictMapErrors["length_name_bigger_fifty"]
    other_errors=dictMapErrors["other_errors"]
    new_users=dictMapErrors["new_users"]
    removed_users=dictMapErrors["removed_users"]
    orga_context_added=dictMapErrors["organ_context_added"]
    orga_context_removed=dictMapErrors["orga_context_removed"]
    new_thirdParty_organ=dictMapErrors["new_thirdParty_organ"]
    removed_thirdParty_orga=dictMapErrors["removed_thirdParty_orga"]
    user_data_changed=dictMapErrors["user_data_changed"]
    roles_differents=dictMapErrors["roles_differents"]
    admin_roles=dictMapErrors["admin_roles"]
    dict_context_roles_users=dictMapErrors["dict_context_roles_users"]


    with open(json_file) as file_to_read:
        data = json.load(file_to_read)
        if type(data) is list:
            print (json_file +" is not a result from migration")
        elif "status" in data.keys() and data["status"]=="failed":
            countfailed+=1
            user_id=getIdFromJson(data)
            message=data["statusDetails"]["message"]
            if isKnownError(message):
                if "User does not exist"==message:
                    missing_users.append(user_id)
                if message=="Schema validation error\n[Error] Element length must be lower or equal to 50!":
                    length_name_bigger_fifty.append(user_id)
                elif "[USER DIFFERENCES]" in message:
                    if IsKnownUserDiffError(message):
                        if "Organizational Context added" in message or "Organizational Context removed" in message:
                            orga_context_added,orga_context_removed=treatOrgaContextChanged(orga_context_added,orga_context_removed,message,user_id)
                        if ("Communication Channel" in message or "First Name is incorrect" in message or "Last Name is incorrect" in message):
                            user_data_changed.append(user_id)
                        if "Roles are different" in message:
                            roles_differents,dict_context_roles_users,admin_roles=treatRolesDifferent(message,user_id,roles_differents,dict_context_roles_users,admin_roles)
                    else:
                        other_errors[user_id]=message
                elif "Context" in message:
                    if "not exists" in message:
                        context = message.split("'",2)[1]
                        if context not in dict_context_missing.keys():
                            dict_context_missing[context]=[]
                        dict_context_missing[context].append(user_id)
                        total_of_failures_missing_context+=1
                    else:
                        other_errors[user_id]=message
                elif message=="[NEW USER]":
                    new_users.append(user_id)
                elif message=="[REMOVED USER]":
                    removed_users.append(user_id)
                elif message=="[NEW ORGANIZATION]":
                    new_thirdParty_organ.append(user_id)
                elif message=="[REMOVED ORGANIZATION]":
                  removed_thirdParty_orga.append(user_id)
            else:
                other_errors[user_id]=message



    dictMapErrors["dict_context_missing"]=dict_context_missing
    dictMapErrors["missing_users"]=missing_users
    dictMapErrors["length_name_bigger_fifty"]=length_name_bigger_fifty
    dictMapErrors["other_errors"]=other_errors
    dictMapErrors["new_users"]=new_users
    dictMapErrors["removed_users"]=removed_users
    dictMapErrors["organ_context_added"]=orga_context_added
    dictMapErrors["orga_context_removed"]=orga_context_removed
    dictMapErrors["new_thirdParty_organ"]=new_thirdParty_organ
    dictMapErrors["removed_thirdParty_orga"]=removed_thirdParty_orga
    dictMapErrors["user_data_changed"]=user_data_changed
    dictMapErrors["roles_differents"]=roles_differents
    dictMapErrors["admin_roles"]=admin_roles
    dictMapErrors["dict_context_roles_users"]=dict_context_roles_users
    return dictMapErrors,total_of_failures_missing_context,countfailed

def countandCreateErrorsMessages(dictMapErrors,total_of_failures_missing_context,countfailed):
    dict_context_missing=dictMapErrors["dict_context_missing"]
    missing_users=dictMapErrors["missing_users"]
    length_name_bigger_fifty=dictMapErrors["length_name_bigger_fifty"]
    other_errors=dictMapErrors["other_errors"]
    new_users=dictMapErrors["new_users"]
    removed_users=dictMapErrors["removed_users"]
    organ_context_added=dictMapErrors["organ_context_added"]
    orga_context_removed=dictMapErrors["orga_context_removed"]
    new_thirdParty_organ=dictMapErrors["new_thirdParty_organ"]
    removed_thirdParty_orga=dictMapErrors["removed_thirdParty_orga"]
    user_data_changed=dictMapErrors["user_data_changed"]
    roles_differents=dictMapErrors["roles_differents"]
    admin_roles=dictMapErrors["admin_roles"]
    dict_context_roles_users=dictMapErrors["dict_context_roles_users"]
    
    number_errors=OrderedDict()
    number_errors["failures_missing_context"]=total_of_failures_missing_context
    number_errors["unique_failures_missing_context"]=len(dict_context_missing)
    number_errors["missing_users_errors"]=len(missing_users)
    number_errors["length_bigger_errors"]=len(length_name_bigger_fifty)
    number_errors["new_users"]=len(new_users)
    number_errors["removed_users"]=len(removed_users)
    number_errors["organ_context_added"]=len(organ_context_added)
    number_errors["orga_context_removed"]=len(orga_context_removed)
    number_errors["new_thirdParty_organ"]=len(new_thirdParty_organ)
    number_errors["removed_thirdParty_orga"]=len(removed_thirdParty_orga)
    number_errors["user_data_changed"]=len(user_data_changed)
    number_errors["roles_differents"]=len(roles_differents)
    number_errors["admin_roles"]=len(admin_roles)
    number_errors["dict_context_roles_users"]=len(dict_context_roles_users)
    number_errors["other_errors"]=len(other_errors)

    total=0
    for error in number_errors:
        if error!="unique_failures_missing_context" and error!="admin_roles" :
            total+=number_errors[error]
    number_errors["total_errors"]=total
    number_errors["total_users_errors"]=countfailed

    error_messages=[]
    error_messages.append(str(number_errors["total_errors"])+" total errors")
    error_messages.append(str(number_errors["total_users_errors"])+" users errors")
    error_messages.append(str(number_errors["failures_missing_context"])+" errors with missing contexts")
    error_messages.append(str(number_errors["unique_failures_missing_context"])+" unique contexts missing")
    error_messages.append(str(number_errors["missing_users_errors"])+" errors of missing users")
    error_messages.append(str(number_errors["length_bigger_errors"])+" errors of elements length bigger than 50")
    error_messages.append(str(number_errors["new_users"])+" new users")
    error_messages.append(str(number_errors["removed_users"])+" removed users")
    error_messages.append(str(number_errors["organ_context_added"])+" unique organanizational context added")
    error_messages.append(str(number_errors["orga_context_removed"])+" unique organanizational context removed")
    error_messages.append(str(number_errors["new_thirdParty_organ"])+" users have a new thirdparty organization")
    error_messages.append(str(number_errors["removed_thirdParty_orga"])+" users have a thirdparty organization removed")
    error_messages.append(str(number_errors["user_data_changed"])+" users have seen their data changed")
    error_messages.append(str(number_errors["roles_differents"])+" users have seen their roles changed")
    error_messages.append(str(number_errors["admin_roles"])+" roles have been changed")
    error_messages.append(str(number_errors["dict_context_roles_users"])+" unique contexts roles changed")
    error_messages.append(str(number_errors["other_errors"])+" other errors")
    return number_errors,error_messages

def printAndSaveReportErrorMessages(path_to_past_results,error_messages):
    with open(path_to_past_results+'global report of errors','w') as f:
        for error in error_messages:
            f.write("%s\n" % error)
            print(error)
    print("Check Results_Job folders to see results in details")

def createFilesResults(path_to_past_results,error_messages,number_errors,dictMapErrors):
    printAndSaveReportErrorMessages(path_to_past_results,error_messages)
    createFilesResultsByErrorTypes(path_to_past_results,number_errors,dictMapErrors)

def createFilesResultsByErrorTypes(path_to_past_results,number_errors,dictMapErrors):
    dict_context_missing=dictMapErrors["dict_context_missing"]
    missing_users=dictMapErrors["missing_users"]
    length_name_bigger_fifty=dictMapErrors["length_name_bigger_fifty"]
    other_errors=dictMapErrors["other_errors"]
    new_users=dictMapErrors["new_users"]
    removed_users=dictMapErrors["removed_users"]
    organ_context_added=dictMapErrors["organ_context_added"]
    organ_context_removed=dictMapErrors["orga_context_removed"]
    new_thirdParty_organ=dictMapErrors["new_thirdParty_organ"]
    removed_thirdParty_orga=dictMapErrors["removed_thirdParty_orga"]
    user_data_changed=dictMapErrors["user_data_changed"]
    roles_differents=dictMapErrors["roles_differents"]
    dict_context_roles_users=dictMapErrors["dict_context_roles_users"]

    with open(path_to_past_results+'contexts_with_roles_changed_and_number_users.json','w') as f:
        f.write("%s" % str(number_errors["dict_context_roles_users"])+" errors. \nList of context with diff of roles and users\n\n")
        json.dump(dict_context_roles_users, f,indent=2, separators=(',', ': '),ensure_ascii=True)


    with open(path_to_past_results+'context_missing_with_users.txt','w') as f:
        f.write("%s" % str(number_errors["failures_missing_context"])+" errors. \nList of context with users attached with error message : User not migrated correctly. Check the errors: Amount of errors: 1\n1 Context XXXX not exists\n\n")
        json.dump(dict_context_missing, f,indent=2, separators=(',', ': '),ensure_ascii=True)

    with open(path_to_past_results+'unique_context_missing.txt','w') as f:
        f.write("%s" % str(number_errors["unique_failures_missing_context"]) +" errors. \nList of unique context with error message : User not migrated correctly. Check the errors: Amount of errors: 1\n1 Context XXXX not exists\n\n")
        for item in dict_context_missing.keys():
            f.write("%s\n" % item)

    with open(path_to_past_results+'user_missing.txt','w') as f:
        f.write("%s" % str(number_errors["missing_users_errors"])+" errors. \nList of id with error message : User does not exist")
        for item in missing_users:
            f.write("%s\n" % item)

    with open(path_to_past_results+'length_element_bigger.txt','w') as f:
        f.write("%s" % str(number_errors["length_bigger_errors"])+" errors. \nList of id with error message : 'Schema validation error\n[Error] Element length must be lower or equal to 50!'")
        for item in length_name_bigger_fifty:
            f.write("%s\n" % item)

    with open(path_to_past_results+'others_errors.json', 'w') as fp:
        fp.write("%s" % str(number_errors["other_errors"])+" errors. \nList of all others errors")
        json.dump(other_errors, fp,indent=2, separators=(',', ': '),ensure_ascii=True)

    with open(path_to_past_results+'new_users.txt','w') as f:
        f.write("%s" % str(number_errors["new_users"])+" errors. \nList of id with error message : 'New users'")
        for item in new_users:
            f.write("%s\n" % item)
    
    with open(path_to_past_results+'removed_users.txt','w') as f:
        f.write("%s" % str(number_errors["removed_users"])+" errors. \nList of id with error message : removed users'")
        for item in removed_users:
            f.write("%s\n" % item)

    with open(path_to_past_results+'organ_context_added.json','w') as f:
        f.write("%s" % str(number_errors["organ_context_added"])+" errors. \nList all id with error message : organization context added")
        json.dump(organ_context_added, f,indent=2, separators=(',', ': '),ensure_ascii=True)

    with open(path_to_past_results+'organ_context_removed.json','w') as f:
        f.write("%s" % str(number_errors["organ_context_added"])+" errors. \nList all id with error message : organization context added")
        json.dump(organ_context_removed, f,indent=2, separators=(',', ': '),ensure_ascii=True)

    with open(path_to_past_results+'new_thirdParty_organ.txt','w') as f:
        f.write("%s" % str(number_errors["new_thirdParty_organ"])+" errors. \nList of id with error message : New ThirdParty Organization")
        for item in new_thirdParty_organ:
            f.write("%s\n" % item)

    with open(path_to_past_results+'removed_thirdParty_orga.txt','w') as f:
        f.write("%s" % str(number_errors["removed_thirdParty_orga"])+" errors. \nList of id with error message : removed_thirdParty_orga")
        for item in removed_thirdParty_orga:
            f.write("%s\n" % item)

    with open(path_to_past_results+'user_data_changed.txt','w') as f:
        f.write("%s" % str(number_errors["user_data_changed"])+" errors. \nList of id with error message : user_data_changed")
        for item in length_name_bigger_fifty:
            f.write("%s\n" % item)

    with open(path_to_past_results+'roles_differents.txt','w') as f:
        f.write("%s" % str(number_errors["roles_differents"])+" errors. \nList of id with error message : roles_differents")
        for item in user_data_changed:
            f.write("%s\n" % item)


def ProcessCheckResults(path_allure_results):

    list_allure_results_folders = listAllAllureResultsFolder(path_allure_results)
    number_part=len(list_allure_results_folders)
    path_to_past_results=createFolderForCheckingResults()


    dictMapErrors={}
    dictMapErrors["dict_context_missing"]={}
    dictMapErrors["missing_users"]=[]
    dictMapErrors["length_name_bigger_fifty"]=[]
    dictMapErrors["other_errors"]={}
    dictMapErrors["new_users"]=[]
    dictMapErrors["removed_users"]=[]
    dictMapErrors["organ_context_added"]={}
    dictMapErrors["orga_context_removed"]={}
    dictMapErrors["new_thirdParty_organ"]=[]
    dictMapErrors["removed_thirdParty_orga"]=[]
    dictMapErrors["user_data_changed"]=[]
    dictMapErrors["roles_differents"]=[]
    dictMapErrors["admin_roles"]=[]
    dictMapErrors["dict_context_roles_users"]={}




    total_of_failures_missing_context=0
    countfailed=0
    for allure_results_folder in list_allure_results_folders:

        list_json_files = [allure_results_folder+ f for f in os.listdir(allure_results_folder) if ".json" in f]

        for json_file in list_json_files:

            dictMapErrors,total_of_failures_missing_context,countfailed=treat_json_file_results(json_file,dictMapErrors,total_of_failures_missing_context,countfailed)

    
    number_errors,error_messages=countandCreateErrorsMessages(dictMapErrors,total_of_failures_missing_context,countfailed)



    createFilesResults(path_to_past_results,error_messages,number_errors,dictMapErrors)

"""
if len(sys.argv) < 2:
    print("Check results errors from migration with json files in allure-results folders.\nusage: python check_results_migration.py <folder with all allure_results directory>")
    sys.exit(1)

path_allure_results=sys.argv[1]"""
path_allure_results="/Users/nael/Work/Migration/Results2"
ProcessCheckResults(path_allure_results)