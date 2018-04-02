from conans import ConanFile, tools, AutoToolsBuildEnvironment
import os
import platform

class GettextConan(ConanFile):
    name = 'gettext'

    source_version = '0.19.8.1'
    package_version = '3'
    version = '%s-%s' % (source_version, package_version)

    requires = 'llvm/3.3-2@vuo/stable', \
               'vuoutils/1.0@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/vuo/conan-gettext'
    license = 'https://www.gnu.org/software/gettext/manual/html_node/GNU-LGPL.html'
    description = 'Helps other GNU packages produce multi-lingual messages'
    source_dir = 'gettext-%s' % source_version
    build_dir = '_build'
    libs = {
        'intl': 0,
    }

    def requirements(self):
        if platform.system() == 'Linux':
            self.requires('patchelf/0.10pre-1@vuo/stable')
        elif platform.system() != 'Darwin':
            raise Exception('Unknown platform "%s"' % platform.system())

    def source(self):
        # The .xz and .lz archives are much smaller, but Conan doesn't yet support those archive formats.
        # https://github.com/conan-io/conan/issues/52
        tools.get('https://ftp.gnu.org/pub/gnu/gettext/gettext-%s.tar.gz' % self.source_version,
                  sha256='ff942af0e438ced4a8b0ea4b0b6e0d6d657157c5e2364de57baa279c1c125c43')

        self.run('mv %s/gettext-runtime/intl/COPYING.LIB %s/libintl.txt' % (self.source_dir, self.source_dir))

    def build(self):
        import VuoUtils
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            autotools = AutoToolsBuildEnvironment(self)

            # The LLVM/Clang libs get automatically added by the `requires` line,
            # but this package doesn't need to link with them.
            autotools.libs = []

            autotools.flags.append('-Oz')

            if platform.system() == 'Darwin':
                autotools.flags.append('-mmacosx-version-min=10.10')
                autotools.link_flags.append('-Wl,-install_name,@rpath/libintl.dylib')

            env_vars = {
                'CC' : self.deps_cpp_info['llvm'].rootpath + '/bin/clang',
                'CXX': self.deps_cpp_info['llvm'].rootpath + '/bin/clang++',
            }
            with tools.environment_append(env_vars):
                autotools.configure(configure_dir='../%s' % self.source_dir,
                                    args=['--quiet',
                                          '--disable-c++',
                                          '--disable-curses',
                                          '--disable-java',
                                          '--disable-static',
                                          '--enable-shared',
                                          '--prefix=%s' % os.getcwd()])
                autotools.make(args=['install'])

            if platform.system() == 'Linux':
                with tools.chdir('lib'):
                    self.run('mv preloadable_libintl.so libintl.so')
                    self.run('chmod +x libintl.so')
                    VuoUtils.fixLibs(self.libs, self.deps_cpp_info)

    def package(self):
        if platform.system() == 'Darwin':
            libext = 'dylib'
        elif platform.system() == 'Linux':
            libext = 'so'

        self.copy('*.h', src='%s/include' % self.build_dir, dst='include')
        self.copy('libintl.%s' % libext, src='%s/lib' % self.build_dir, dst='lib')

        self.copy('libintl.txt', src=self.source_dir, dst='license')

    def package_info(self):
        self.cpp_info.libs = ['intl']
