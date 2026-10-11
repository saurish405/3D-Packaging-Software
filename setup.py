import os
import sys
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

class get_pybind_include(object):
    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)

ext_modules = [
    Extension(
        'optimizer_cpp',
        [
            'optimizer/cpp/collision.cpp',
            'optimizer/cpp/placement.cpp',
            'optimizer/cpp/layer.cpp',
            'optimizer/cpp/gravity.cpp',
            'optimizer/cpp/rotations.cpp',
            'optimizer/cpp/search.cpp',
            'optimizer/cpp/scoring.cpp',
            'optimizer/cpp/optimizer.cpp',
            'optimizer/cpp/pybind_module.cpp',
        ],
        include_dirs=[
            get_pybind_include(),
            get_pybind_include(user=True),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'optimizer', 'cpp')
        ],
        language='c++'
    ),
]

class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc', '/std:c++20', '/O2'],
        'unix': ['-std=c++20', '-O3'],
        'mingw32': ['-std=c++20', '-O3'],
    }
    l_opts = {
        'msvc': [],
        'unix': [],
        'mingw32': ['-static-libgcc', '-static-libstdc++'],
    }

    def build_extensions(self):
        ct = self.compiler.compiler_type
        # Default options based on compiler type
        opts = self.c_opts.get(ct, [])
        link_opts = self.l_opts.get(ct, [])

        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version())

        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts

        build_ext.build_extensions(self)

setup(
    name='optimizer_cpp',
    version='0.1.0',
    description='C++ optimization bindings for 3D packaging solver',
    ext_modules=ext_modules,
    setup_requires=['pybind11>=2.5.0'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
)
