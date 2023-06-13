from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

setup(
    name="sampling",
    ext_modules=[
        CUDAExtension("sampling", [
            "sampling_gather.cu",
            "sampling_fps.cu",
            "sampling.cpp",
        ]),
    ],
    cmdclass={
        "build_ext": BuildExtension
    })