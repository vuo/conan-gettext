from conans import ConanFile, tools, AutoToolsBuildEnvironment
import os

class GettextConan(ConanFile):
    name = 'gettext'
    version = '0.19.8.1'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/vuo/conan-gettext'
    license = 'https://www.gnu.org/software/gettext/manual/html_node/GNU-LGPL.html'
    description = 'Helps other GNU packages produce multi-lingual messages'
    source_dir = 'gettext-%s' % version
    build_dir = '_build'

    def source(self):
        # The .xz and .lz archives are much smaller, but Conan doesn't yet support those archive formats.
        # https://github.com/conan-io/conan/issues/52
        tools.get('https://ftp.gnu.org/pub/gnu/gettext/gettext-%s.tar.gz' % self.version,
                  sha256='ff942af0e438ced4a8b0ea4b0b6e0d6d657157c5e2364de57baa279c1c125c43')

    def build(self):
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            autotools = AutoToolsBuildEnvironment(self)
            autotools.cxx_flags.append('-Oz')
            autotools.cxx_flags.append('-mmacosx-version-min=10.8')
            autotools.link_flags.append('-Wl,-install_name,@rpath/libintl.dylib')
            autotools.configure(configure_dir='../%s' % self.source_dir,
                                args=['--quiet',
                                      '--disable-c++',
                                      '--disable-curses',
                                      '--disable-java',
                                      '--disable-static',
                                      '--enable-shared',
                                      '--prefix=%s' % os.getcwd()])
            autotools.make(args=['install'])

    def package(self):
        self.copy('*.h', src='%s/include' % self.build_dir, dst='include')
        self.copy('libintl.dylib', src='%s/lib' % self.build_dir, dst='lib')

    def package_info(self):
        self.cpp_info.libs = ['intl']
