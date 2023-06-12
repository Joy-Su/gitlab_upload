#!/home/kouwenbo/conda/envs/r4.0/bin/python

# coding=utf-8
import requests
import argparse
import os
import base64
import datetime
from oebio.tools.record import Record
# import click

# poppler installed and in PATH
# os.environ['PATH'] = f"/home/kouwenbo/conda/envs/r4.0/bin:{os.environ['PATH']}"





#传参
# parser = argparse.ArgumentParser() #创建解析对象
# parser.add_argument("-i", "--inputt", help = "inputt file[directory]")
# parser.add_argument("-o", "--out", help = "inputt output file[directory]")
# parser.add_argument("-s", "--script", help = "script file[directory]")
# parser.add_argument("-p", "--project", help = "function label,seperate by ',' ")
# parser.add_argument("-pn", "--projectnum", help = "description of project")
# parser.add_argument("-n", "--name", help = "上传人员名字")
# parser.add_argument("-g", "--group", help = "dna rna development multiomics common")
# parser.add_argument("-desc", "--description", help = "description of project")
# parser.add_argument("-m", "--make", help = "whether to make a repository, T or F ,default:T", default = "T")
# parser.add_argument("-id", "--idn", help = "需要推送的仓库id号")
#
# args = parser.parse_args()
# inputt = args.inputt
# out = args.out
# script = args.script
# project = args.project
# project_num = args.projectnum
# name = args.name
# group = args.group
# description = args.description
# date = datetime.datetime.now().strftime("%Y%m%d")
# make = args.make
# idn = args.idn

with open('/home/sujieyi/anaconda3/envs/python3.9/lib/python3.9/site-packages/oebio-1.1.7-py3.9.egg/oebio/tools/config') as f:
    env_ls=f.read()

def send_requests(key_word, url_api, token, description, id):

    response = requests.post(url=url_api,
                             json={"name": key_word, "description": description, "initialize_with_readme": "true", "namespace_id": str(id)},
                             headers={"Content-Type": "application/json", "PRIVATE-Token": token})

    if response.status_code == 201:
        result_json = response.json()
        id = result_json.get('id')
        print ('仓库创建成功！'+' id为：'+str(id))
        return id
    else:
        print (str(response.status_code)+'创建失败')


def action_dic(directory, filename, content, encoding = 'text'):
    dic = {"action": "create",
                    "file_path": '/'.join([directory, filename]),
                    "content": content,
                    "encoding": encoding}
    return dic

def action_request(url_api, id, token, name, ls):
    action = requests.post(url = url_api+str(id)+'/repository/commits',
                           headers={"Content-Type": "application/json", "PRIVATE-Token": token},
                           json = {"branch": "main","commit_message": "Initial commit" ,"author_name": name,
                                   "actions": ls
                                   })

    if action.status_code == 201:
        print ('文件推送成功！')
    else:
        print (str(action.status_code) + '文件推送失败')
    return action.status_code


def file_size(input):
    inputt_size = 0
    for i, j, k in os.walk(input):
        inputt_size += sum([os.path.getsize(os.path.join(i, name)) for name in k])
    return inputt_size


def file_ergodic(file):
    filelist = []
    img = []
    for i,j,k in os.walk(file):
        for filename in k:
            if filename.endswith('.pdf') or filename.endswith('.png'):
                img.append(os.path.join(i,filename))
            else:
                filelist.append(os.path.join(i,filename))
    return filelist,img

def run_action_request(directory, infile_ls):
    inputt_ls = []
    for i in infile_ls[0]:
        f = open(i)
        temp_dict = action_dic(directory, i.split('/')[-1], f.read(), encoding='text')
        f.close()
        inputt_ls.append(temp_dict)

    if len(infile_ls[1]) == 0:
        pass
    else:
        for i in infile_ls[1]:
            f = open(i, 'rb')
            f_file = f.read()
            base_64_encoded_data = base64.b64encode(f_file)
            base64_message = base_64_encoded_data.decode('utf-8')
            temp_dict = action_dic(directory, i.split('/')[-1], base64_message, encoding='base64')
            inputt_ls.append(temp_dict)
            f.close()
    return inputt_ls

# @click.command('api_git')
# @click.option('-i', '--input', prompt = 'your input', help = '需要上传的输入文件[目录]')
# @click.option('-o', '--out', help = '需要上传的输出文件[目录],图片只接受png格式')
# @click.option('-s', '--script', help = '需要上传的脚本[目录]')
# @click.option('-p','--project', help = '功能标签, 请用英文逗号隔开！！！')
# @click.option('-pn', '--project_num', help = '项目编号')
# @click.option('-n', '--name', help = '上传人员名字')
# @click.option('-g', '--group', help = 'dna rna development multiomics common')
# @click.option('-desc', '--description', help = '项目简要描述')
# @click.option('-m', '--make', help = '是否需要创建仓库, 默认 T', default = 'T')
# @click.option('-id', '--idn', help = '如果不需要创建仓库, 则需传入仓库id')

def api_git(input, out, script, project, project_num, name, group, description, make, idn):
    date = datetime.datetime.now().strftime("%Y%m%d")
    key_word = '_'.join([project.replace(",", "_"), project_num, date, name])
    print (key_word)
    group_list = {'development': ['235', 'http://gitlab.oebiotech.cn/Development/temporary/' + key_word],
                  'dna': ['377', 'http://gitlab.oebiotech.cn/business/dna/subsequentanalysis/' + key_word],
                  'rna': ['376', 'http://gitlab.oebiotech.cn/business/rna/subsequentanalysis/' + key_word],
                  'multiomics': ['293',
                                 'http://gitlab.oebiotech.cn/business/multiomics/subsequentanalysis/' + key_word],
                  'common': ['375', 'http://gitlab.oebiotech.cn/business/common/subsequentanalysis/' + key_word]}

    url_api = 'http://gitlab.oebiotech.cn/api/v4/projects/'
    token = env_ls.split('\n')[0].split('=')[1]
    idd = group_list.get(group, ' ')[0]
    if idd == ' ':
        print('group 参数无效！无法建立仓库')
    url = group_list.get(group)[1]
    input = os.path.abspath(input)
    out = os.path.abspath(out)
    script = os.path.abspath(script)
    print(input)
    print(out)
    print(script)
    if make == 'T':
        id = send_requests(key_word, url_api, token, description, idd)
        print ('此时id为'+str(id))
    else:
        id = idn
        print ('仓库id为：'+str(id))
    inputt_size = file_size(input)
    output_size = file_size(out)
    img = []
    if inputt_size <= 2097152 and output_size <= 2097152:
        inputt_file = file_ergodic(input)
        output_file = file_ergodic(out)
        script_file = file_ergodic(script)
        img.extend(inputt_file[1])
        img.extend(output_file[1])
        img.extend(script_file[1])
        total_list = []
        total_list.extend(run_action_request('data', inputt_file))
        total_list.extend(run_action_request('out', output_file))
        total_list.extend(run_action_request('script', script_file))
        backup = []

    else:
        script_file = file_ergodic(script)
        img.extend(script_file[1])
        total_list = run_action_request('script',script_file)
        backup = [input, out, script]
    submit_status = action_request(url_api, id, token, name, total_list)
    if submit_status == 201:
        
    	rcd = Record(
        	name = '_'.join([project, project_num, date, name]),
        	keyword = [project, project_num],
        	summary = description,
        	url = url,
        	img = img,
        	mail = name,
        	path = env_ls.split('\n')[1].split('=')[1],
        	backup = backup,
        	bkprefix = env_ls.split('\n')[2].split('=')[1]
    	)
    	rcd.repo_html()
    	rcd.index_html()


if __name__ == '__main__':
    api_git()
