from __future__ import absolute_import
from collections import namedtuple
import contextlib
import os
import shutil
from string import Template
from tempfile import mkdtemp
from six.moves.urllib.request import urlretrieve

from planemo import galaxy_run
from galaxy.tools.deps import commands

WEB_SERVER_CONFIG_TEMPLATE = """
[server:main]
use = egg:Paste#http
port = ${port}
host = ${host}
use_threadpool = True
threadpool_kill_thread_limit = 10800
[app:main]
paste.app_factory = galaxy.web.buildapp:app_factory
"""

TOOL_CONF_TEMPLATE = """<toolbox>
  <section id="data_source" name="Data Source">
    <tool file="data_source/upload.xml" />
  </section>
  <section id="testing" name="Test Tools">
    ${tool_definition}
  </section>
</toolbox>
"""

EMPTY_TOOL_CONF_TEMPLATE = """<toolbox></toolbox>"""

DOWNLOADS_URL = "https://github.com/jmchilton/galaxy-downloads/raw/master/"
DATABASE_TEMPLATE_URL = DOWNLOADS_URL + "db_gx_rev_0120.sqlite"

FAILED_TO_FIND_GALAXY_EXCEPTION = (
    "Failed to find Galaxy root directory - please explicitly specify one "
    "with --galaxy_root."
)

GalaxyConfig = namedtuple(
    'GalaxyConfig',
    ['galaxy_root', 'config_directory', 'env']
)


def find_galaxy_root(**kwds):
    galaxy_root = kwds.get("galaxy_root", None)
    if galaxy_root:
        return galaxy_root
    else:
        par_dir = os.getcwd()
        while True:
            run = os.path.join(par_dir, "run.sh")
            config = os.path.join(par_dir, "config")
            if os.path.isfile(run) and os.path.isdir(config):
                return par_dir
            new_par_dir = os.path.dirname(par_dir)
            if new_par_dir == par_dir:
                break
            par_dir = new_par_dir
    raise Exception(FAILED_TO_FIND_GALAXY_EXCEPTION)


def find_test_data(path, **kwds):
    # Find test data directory associated with path.
    test_data = kwds.get("test_data", None)
    if test_data:
        return os.path.abspath(test_data)
    else:
        if not os.path.isdir(path):
            tool_dir = os.path.dirname(path)
        else:
            tool_dir = path
        for possible_dir in [tool_dir, "."]:
            test_data = os.path.join(possible_dir, "test-data")
            if os.path.exists(test_data):
                return test_data
    return None


@contextlib.contextmanager
def galaxy_config(tool_path, **kwds):
    if kwds.get("install_galaxy", None):
        galaxy_root = None
    else:
        galaxy_root = find_galaxy_root(**kwds)

    config_directory = kwds.get("config_directory", None)

    def config_join(*args):
        return os.path.join(config_directory, *args)

    created_config_directory = False
    if not config_directory:
        created_config_directory = True
        config_directory = mkdtemp()
    try:
        if kwds.get("install_galaxy", None):
            install_cmds = [
                galaxy_run.DEACTIVATE_COMMAND,
                "cd %s" % config_directory,
                galaxy_run.DOWNLOAD_GALAXY,
                "tar -zxvf master | tail",
                "cd galaxy-central-master",
                "virtualenv .venv",
                ". .venv/bin/activate; sh scripts/common_startup.sh"
            ]
            commands.shell(";".join(install_cmds))
            galaxy_root = config_join("galaxy-central-master")

        tool_path = os.path.join(tool_path)
        if os.path.isdir(tool_path):
            tool_definition = '''<tool_dir dir="%s" />'''
        else:
            tool_definition = '''<tool file="%s" />'''

        empty_tool_conf = config_join("empty_tool_conf.xml")
        tool_conf = config_join("tool_conf.xml")
        database_location = config_join("galaxy.sqlite")
        preseeded_database = True
        try:
            urlretrieve(DATABASE_TEMPLATE_URL, database_location)
        except Exception:
            preseeded_database = False

        template_args = dict(
            port=kwds.get("port", 9090),
            host="127.0.0.1",
            temp_directory=config_directory,
            database_location=database_location,
            tool_definition=tool_definition % tool_path,
            tool_conf=tool_conf,
            debug=kwds.get("debug", "true"),
            master_api_key=kwds.get("master_api_key", "test_key"),
            id_secret=kwds.get("id_secret", "test_secret"),
            log_level=kwds.get("log_level", "DEBUG"),
        )
        properties = dict(
            database_connection=("sqlite:///${database_location}?"
                                 "isolation_level=IMMEDIATE"),
            file_path="${temp_directory}files",
            new_file_path="${temp_directory}/tmp",
            tool_config_file=tool_conf,
            check_migrate_tools="False",
            manage_dependency_relationships="False",
            job_working_directory="${temp_directory}/job_working_directory",
            template_cache_path="${temp_directory}/compiled_templates",
            citation_cache_type="file",
            citation_cache_data_dir="${temp_directory}/citations/data",
            citation_cache_lock_dir="${temp_directory}/citations/lock",
            collect_outputs_from="job_working_directory",
            database_auto_migrate="True",
            cleanup_job="never",
            master_api_key="${master_api_key}",
            id_secret="${id_secret}",
            log_level="${log_level}",
            debug="${debug}",
            integrated_tool_panel_config=("${temp_directory}/"
                                          "integrated_tool_panel_conf.xml"),
            migrated_tools_config=empty_tool_conf,
        )
        # TODO: consider following property
        # tool_dependency_dir = None
        # watch_tools = False
        # datatypes_config_file = config/datatypes_conf.xml
        # welcome_url = /static/welcome.html
        # logo_url = /
        # sanitize_all_html = True
        # serve_xss_vulnerable_mimetypes = False
        # job_config_file = config/job_conf.xml
        # track_jobs_in_database = None
        # outputs_to_working_directory = False
        # retry_job_output_collection = 0

        env = {}
        for key, value in properties.iteritems():
            var = "GALAXY_CONFIG_OVERRIDE_%s" % key.upper()
            value = __sub(value, template_args)
            env[var] = value
        # No need to download twice - would GALAXY_TEST_DATABASE_CONNECTION
        # work?
        if preseeded_database:
            env["GALAXY_TEST_DB_TEMPLATE"] = DATABASE_TEMPLATE_URL
        env["GALAXY_TEST_MIGRATED_TOOL_CONF"] = empty_tool_conf
        env["GALAXY_TEST_SHED_TOOL_CONF"] = empty_tool_conf
        env["GALAXY_TEST_TOOL_CONF"] = tool_conf

        web_config = __sub(WEB_SERVER_CONFIG_TEMPLATE, template_args)
        open(config_join("galaxy.ini"), "w").write(web_config)
        tool_conf_contents = __sub(TOOL_CONF_TEMPLATE, template_args)
        open(tool_conf, "w").write(tool_conf_contents)
        open(empty_tool_conf, "w").write(EMPTY_TOOL_CONF_TEMPLATE)

        yield GalaxyConfig(galaxy_root, config_directory, env)
    finally:
        if created_config_directory:
            shutil.rmtree(config_directory)


def __sub(template, args):
    return Template(template).safe_substitute(args)
