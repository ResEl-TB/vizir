"""This module processes Vizir files"""


import os
import glob
import hashlib
from distutils import dir_util, file_util

import yaml
from git import Repo, GitCommandError
from jinja2 import Environment, FileSystemLoader
from sphinx.cmd import build

from .constants import REMOTE
from .util import err, header, Step, mag, warn, Section


def get_field(field, dic, default = "", transform = lambda x: x):
    """
    Get a value in a dictionary and transform it if it the given key exists or return a default
    value
    :param field: The key
    :param dic: The dictionary
    :param default: The default value to return
    :param transform: The transformation to apply
    """
    return transform(dic[field]) if field in dic else default

def auto_list(arg):
    """
    Put the argument in a list if it is not itself a list
    :param arg: The argument
    """
    if not isinstance(arg, list):
        return [arg]
    return arg

def md5_hash(string):
    """
    Computes the MD5 hash of the given string
    :param string: The string to hash
    """
    return hashlib.md5(string.encode("utf8")).hexdigest()

def get_resources(dic, path):
    """
    Get resources locally or remotely
    :param dic: The dictionary describing the resources
    :param path: The base destination path
    """
    dir_util.mkpath(path)

    # If the resources are in a remote repository
    if 'from' in dic:
        temp_path = md5_hash(dic['from'])
        with Step(f'Acquiring {mag(format(dic["from"]))} repository'):
            Repo.clone_from(REMOTE.format(dic['from']), temp_path)
    else:
        temp_path = '.'

    for group in get_field('files', dic, [{}], auto_list):
        destination = get_field('to', group, '.')
        plus = get_field('plus', group, ['*'], auto_list)
        minus = get_field('minus', group, [], auto_list)
        plus_set = set().union(*[glob.glob(os.path.join(temp_path, rule)) for rule in plus])
        minus_set = set().union(*[glob.glob(os.path.join(temp_path, rule)) for rule in minus])
        for match in plus_set.difference(minus_set).difference({'.docs'}):
            dest = os.path.join(path, destination)
            with Step(f'Copying {mag(match)} to {mag(dest)}'):
                if os.path.isfile(match):
                    file_util.copy_file(match, dest)
                else:
                    dir_util.copy_tree(match, os.path.join(dest, os.path.split(match)[-1]))


def merge_fields(first, other, merge):
    """
    Merge the fields from two dictionaries
    :param first: The first dictionary
    :param other: The other dictionary
    :param merge: The merging function
    """
    return dict(list(first.items()) + list(other.items()) +
                [(key, merge(first[key], other[key])) for key in set(first) & set(other)])


def merge_confs(main_conf, new_conf):
    """
    Merge two configurations in place
    :param main_conf: The configuration to be modified
    :param new_conf: The configuration to add
    """
    # Merge the imports
    main_conf['import'] |= set(get_field('import', new_conf, [], auto_list))

    # Merge the variables
    variables = get_field('vars', new_conf, {})
    for i in variables:
        if i in main_conf['vars']:
            warn(f'Overwriting {i}')
        main_conf['vars'][i] = variables[i]

    # Merge the lists
    lists = {key: set(auto_list(val)) for key, val in get_field('lists', new_conf, {}).items()}
    main_conf['lists'] = merge_fields(main_conf['lists'], lists, lambda x, y: x | y)
    main_conf['expr_lists'] = merge_fields(main_conf['expr_lists'],
                                           get_field('expr_lists', new_conf, {}),
                                           lambda x, y: x + '|' + y)


def data_dump(dic, transform = lambda x: x):
    """
    Dump a dictionary as an executable Python script
    :params dic: The dictionary to dump
    :params f: The transformation to apply on the dictionary values
    """
    return '\n'.join(f'{i}={transform(j)}' for (i, j) in dic.items())


def prepare_templates(section, conf, project_conf, project_dir, templates_template):
    """
    Prepare the templates for a section
    :param section: The section name
    :param conf: The section configuration
    :param project_conf: The project configuration
    :param project_dir: The project directory
    :param templates_template: The dynamic template configuration
    """
    with Section(f'Section {section}'):
        with Step('Preparing the templates'):
            for template in get_field('templates', conf, [], auto_list):
                rendered = yaml.safe_load(templates_template.render({'source_path': repr(section)}))
                if template not in rendered:
                    raise BaseException(f'Template {template} not found')
                merge_confs(project_conf, rendered[template])
        get_resources(conf, os.path.join(project_dir, section))


def build_sphinx_config(data, project_conf, docs_dir, conf_template):
    """
    Build the Sphinx configuration file
    :param data: The Python data
    :param project_conf: The project configuration
    :param docs_dir: The documentation directory
    :param conf_template: The configuration file template
    """
    with Step('Building Sphinx configuration'):
        data['imports'] = (f'import {", ".join(project_conf["import"])}'
                           if project_conf['import'] else '')
        data['vars'] = data_dump(project_conf['vars'], repr)
        data['expr_lists'] = data_dump(project_conf['expr_lists'], lambda x: f'list({x})')
        data['lists'] = data_dump(project_conf['lists'], lambda x: repr(list(x)))

        with open(os.path.join(docs_dir, 'conf.py'), 'w', encoding='utf8') as file:
            file.write(conf_template.render(data))


def process_project(project, directory, conf, templates_template, conf_template):
    """
    Process a Vizir project
    :param project: The project name
    :param directory: The base directory
    :param conf: The project configuration
    :param templates_template: The dynamic template configuration
    :param conf_template: The configuration template
    """
    project_conf = {'import': set(), 'vars': {}, 'lists': {}, 'expr_lists': {}}
    project_dir = os.path.join(directory, '.docs', project)
    docs_dir = os.path.join(project_dir, '.docs')
    build_dir = os.path.join(project_dir, '.build')
    os.makedirs(docs_dir)

    with Section(f'Project {project}'):
        with Step(f'Acquiring {mag("target")} repository'):
            build_repo = Repo.clone_from(REMOTE.format(get_field('repo', conf)), build_dir)
            try:
                build_repo.git.rm('-rf', '*')
            except GitCommandError as e:
                warn(f'Exception GitCommandError raised: {e}')

        version = get_field('version', conf)
        data = {'project': project, 'version': version, 'copyright': get_field('copyright', conf),
                'release': get_field('release', conf, version)}
        data = {key: repr(val) for (key, val) in data.items()}

        get_resources(get_field('docs', conf, {'files': {'plus': '*', 'to': '.'}}), docs_dir)

        for sec in get_field('code', conf, []):
            prepare_templates(sec, conf['code'][sec], project_conf, project_dir, templates_template)

        build_sphinx_config(data, project_conf, docs_dir, conf_template)

        cwd = os.getcwd()
        os.chdir(docs_dir)

        locales = get_field('locales', conf, ['fr'], auto_list)
        with Step(f'Generating documentation for the main locale ({mag(locales[0])})',
                  single_line=False):
            if build.main(['.', os.path.join('..', '.build', locales[0])]):
                raise BaseException('An error occurred')

        for locale in locales[1:]:
            with Step(f'Generating documentation for the {mag(locale)} locale', single_line=False):
                if build.main(['.', os.path.join('..', '.build', locale),
                              '-D', f'language={locale}']):
                    raise BaseException('An error occurred')

        with Step('Pushing the target repository', 'Done', single_line=False):
            build_repo.git.add(':!**/.doctrees/*')
            try:
                build_repo.git.commit("-m", "Automatic Vizir modification")
            except GitCommandError as e:
                warn(f'Exception GitCommandError raised: {e}')
            else:
                build_repo.git.push()

        os.chdir(cwd)


def process(directory="."):
    """
    Process a Vizir directory and build the documentation
    :param directory: The directory to process
    """
    header('Vizir Processor')

    try:
        with open(os.path.join(directory, '.docs.yml'), 'r', encoding='utf8') as file:
            conf = yaml.safe_load(file)
    except FileNotFoundError:
        err(f'No {mag(".docs.yml")} file found')

    if os.path.exists(os.path.join(directory, '.docs')):
        err(f'{mag(".docs")} directory already exists')

    env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.realpath(__file__))))
    conf_template = env.get_template('conf.py.j2')
    templates_template = env.get_template('templates.yml')
    for project in conf:
        process_project(project, directory, conf[project], templates_template, conf_template)
