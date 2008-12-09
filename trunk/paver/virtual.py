"""Tasks for managing virtualenv environments."""

from paver.easy import task, options, dry, debug
from paver.path import path
from paver.release import setup_meta

try:
    from paver import ext_poacheggs as poacheggs
    has_poacheggs = True
except ImportError:
    has_poacheggs = False

try:
    import virtualenv
    has_virtualenv = True
except ImportError:
    has_virtualenv = False

if has_virtualenv:
    _easy_install_template = "    subprocess.call([join(%s, 'easy_install'), " \
                                     "'%s'])\n"
    def _create_bootstrap(script_name, packages_to_install, paver_command_line,
                          install_paver=True, more_text=""):
        if install_paver:
            paver_install = (_easy_install_template % 
                        ('bin_dir', 'paver==%s' % setup_meta['version']))
        else:
            paver_install = ""
        
        extra_text = """def adjust_options(options, args):
    args[:] = ['.']

def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin_dir = join(home_dir, 'Scripts')
    else:
        bin_dir = join(home_dir, 'bin')
%s""" % paver_install
        for package in packages_to_install:
            extra_text += _easy_install_template % ('bin_dir', package)
        if paver_command_line:
            command_list = []
            command_list.extend(paver_command_line.split(" "))
            extra_text += "    subprocess.call([join(bin_dir, 'paver'),%s)" % repr(command_list)[1:]

        extra_text += more_text
        bootstrap_contents = virtualenv.create_bootstrap_script(extra_text)
        fn = script_name
        
        debug("Bootstrap script extra text: " + extra_text)
        def write_script():
            open(fn, "w").write(bootstrap_contents)
        dry("Write bootstrap script %s" % (fn), write_script)
        
                
    @task
    def bootstrap():
        """Creates a virtualenv bootstrap script. 
        The script will create a bootstrap script that populates a
        virtualenv in the current directory. The environment will
        have paver, the packages of your choosing and will run
        the paver command of your choice.
        
        This task looks in the virtualenv options for:
        
        script_name
            name of the generated script
        packages_to_install
            packages to install with easy_install. The version of paver that
            you are using is included automatically. This should be a list of
            strings.
        paver_command_line
            run this paver command line after installation (just the command
            line arguments, not the paver command itself).
        """
        vopts = options.virtualenv
        _create_bootstrap(vopts.get("script_name", "bootstrap.py"),
                          vopts.get("packages_to_install", []),
                          vopts.get("paver_command_line", None))

if has_poacheggs:
    @task
    def install_all():
        """Uses PoachEggs to install everything from the requirements
        file.
    
        This task looks in the options for:
    
        requirements
            path of the requirements file (defaults to requirements.txt)
        egg_cache
            optional path to the directory in which eggs will be cached
        cache_only
            only install from the egg cache (default: false)
        environment
            path to the virtualenv that is setup
        """
        options.order('virtualenv', add_rest=True)
        reqfile = options.get("requirements", "requirements.txt")
        cmdopts = ['-r', reqfile]
        egg_cache = options.get("egg_cache")
        if egg_cache:
            cmdopts.extend(['--egg-cache', egg_cache])
        cache_only = options.get('cache_only', False)
        if cache_only:
            cmdopts.append('--cache-only')
        environment = options.get('environment')
        if environment:
            cmdopts.extend(['-E', environment])
        poacheggs.main(cmdopts)
    
    @task
    def freeze():
        """Create a new requirements file with the requirements
        frozen at the present version.
    
        Options:
    
        frozen_file
            path of the frozen requirements file to generate (defaults to frozen.txt)
        environment
            path to the virtualenv that is setup
        """
        options.order('virtualenv', add_rest=True)
        frozenfile = options.get('frozen_file', 'frozen.txt')
        cmdopts = ['--freeze', frozenfile]
        environment = options.get('environment')
        if environment:
            cmdopts.extend(['-E', environment])
        dry("PoachEggs builtin with options: %s" % (cmdopts,), 
            lambda: poacheggs.main(cmdopts))
    