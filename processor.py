#!/usr/bin/python3

import sys
import os
import yaml
import glob
from distutils import dir_util, file_util
import random
import string
from jinja2 import Environment, FileSystemLoader
from git import Repo
import hashlib
import sphinx

remote = "ssh://git.resel.fr:43000/{}"

def get_field(field, dict, default = "", transform = lambda x: x):
    return transform(dict[field]) if field in dict else default

def auto_list(arg):
    if isinstance(arg, str):
        return [arg]
    return arg

def hash(str):
    return hashlib.md5(str.encode("utf8")).hexdigest()

def get_resource(dict, path):
    global remote
    dir_util.mkpath(path)
    if "from" in dict:
        temp_path = hash(dict["from"])
        print("Acquiring repo {}...".format(dict["from"]))
        Repo.clone_from(remote.format(dict["from"]), temp_path)
        print("Done.")
    else:
        temp_path = "."
    plus = get_field("plus", dict, [], auto_list)
    minus = get_field("minus", dict, [], auto_list)
    for match in set().union(*[glob.glob(os.path.join(temp_path, rule)) for rule in plus]).difference(set().union(*[glob.glob(os.path.join(temp_path, rule)) for rule in minus])):
        print("Copying {} to {}".format(match, path))
        if os.path.isfile(match):
            file_util.copy_file(match, path)
        else:
            dir_util.copy_tree(match, os.path.join(path, os.path.split(match)[-1]))

def merge_fields(a, b, f):
    return dict(list(a.items()) + list(b.items()) + [(k, f(a[k], b[k])) for k in set(a) & set(b)])

def merge_confs(main_conf, new_conf):
    main_conf["import"] |= set(get_field("import", new_conf, [], auto_list))
    vars = get_field("vars", new_conf, {})
    for i in vars:
        if i in main_conf["vars"]:
            print("WARNING: overwriting {}".format(i))
        main_conf["vars"][i] = vars[i]
    lists = get_field("lists", new_conf, {})
    for i in lists:
        lists[i] = set(auto_list(lists[i]))
    main_conf["lists"] = merge_fields(main_conf["lists"], lists, lambda x, y: x | y)
    expr_lists = get_field("expr_lists", new_conf, {})
    main_conf["expr_lists"] = merge_fields(main_conf["expr_lists"], expr_lists, lambda x, y: x + "|" + y)

def data_dump(dict, f = lambda x: x):
    return '\n'.join("{}={}".format(i, f(j)) for (i, j) in dict.items())

print("ResEl Documentation Processor\n-----------------------------")

if len(sys.argv) != 2:
    print("Usage: python3 processor.py <directory>")
    sys.exit(1)

try:
    conf = yaml.load(open(os.path.join(sys.argv[1], ".docs.yml"), 'r'))
except Exception as e:
    print(e)
    sys.exit(1)
else:
    env = Environment(loader=FileSystemLoader('.'))
    conf_template = env.get_template('conf.py')
    templates_template = env.get_template('templates.yml')
    for project in conf:
        print("* Project {} found".format(project))
        project_conf = {"import": set(), "vars": {}, "lists": {}, "expr_lists": {}}
        project_dir = os.path.join("doku", project)
        docs_dir = os.path.join(project_dir, ".docs")
        os.makedirs(docs_dir)

        data = {"project": project, "version": get_field("version", conf[project]), "release": get_field("release", conf[project]), "authors": get_field("authors", conf[project]), "copyright": get_field("copyright", conf[project])}
        data = {i:repr(j) for (i,j) in data.items()}

        get_resource(conf[project]["docs"], docs_dir)

        for section in conf[project]["code"]:
            print("|-* Section {} found".format(section))
            temp = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
            get_resource(conf[project]["code"][section], os.path.join(project_dir, temp))
            for i in get_field("templates", conf[project]["code"][section], [], auto_list):
                merge_confs(project_conf, yaml.load(templates_template.render({"source_path": repr(temp)}))[i])
        data["imports"] = "import {}".format(", ".join(project_conf["import"])) if project_conf["import"] else ""
        data["vars"] = data_dump(project_conf["vars"], repr)
        data["expr_lists"] = data_dump(project_conf["expr_lists"], lambda x: "list({})".format(x))
        data["lists"] = data_dump(project_conf["lists"], lambda x: repr(list(x)))
        with open(os.path.join(docs_dir, "conf.py"), 'w') as f:
            f.write(conf_template.render(data))
        os.chdir(docs_dir)

        locales = get_field("locales", conf[project], [], auto_list)
        print("Generating documentation for the main locale: {}".format(locales[0]))
        sphinx.main(["", ".", os.path.join("..", ".build", locales[0])])

        for locale in locales[1:]:
            print("Generating documentation for the locale: {}".format(locale))
            sphinx.main(["", ".", os.path.join("..", ".build", locale), "-D", "language={}".format(locale)])