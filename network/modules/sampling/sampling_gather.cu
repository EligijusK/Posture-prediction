#include <ATen/cuda/CUDAContext.h>
#include <torch/extension.h>

#include <stdio.h>
#include <ATen/ATen.h>

#include <cuda.h>
#include <cuda_runtime.h>

void gatherpointLauncher(int b, int n, int m, const float *inp, const int *idx, float *out);
__global__ void gatherpointKernel(int b, int n, int m, const float *__restrict__ inp, const int *__restrict__ idx,float *__restrict__ out);

void scatteraddpointLauncher(int b, int n, int m, const float *out_g, const int *idx, float *inp_g);
__global__ void scatteraddpointKernel(int b, int n, int m, const float *__restrict__ out_g, const int *__restrict__ idx,float *__restrict__ inp_g);


__global__ void scatteraddpointKernel(int b, int n, int m, const float *__restrict__ out_g, const int *__restrict__ idx,float *__restrict__ inp_g) {
    for (int i = blockIdx.x; i < b; i += gridDim.x) {
        for (int j = blockIdx.y * blockDim.x + threadIdx.x; j < m; j += blockDim.x * gridDim.y) {
            int a = idx[i * m + j];

            atomicAdd(&inp_g[(i * n + a) * 3 + 0], out_g[(i * m + j) * 3 + 0]);
            atomicAdd(&inp_g[(i * n + a) * 3 + 1], out_g[(i * m + j) * 3 + 1]);
            atomicAdd(&inp_g[(i * n + a) * 3 + 2], out_g[(i * m + j) * 3 + 2]);
        }
    }
}

void scatteraddpointLauncher(int b, int n, int m, const float *out_g, const int *idx, float *inp_g) {
    scatteraddpointKernel<<<dim3(2, 8, 1), 512>>>(b, n, m, out_g, idx, inp_g);
}

__global__ void gatherpointKernel(int b, int n, int m, const float *__restrict__ inp, const int *__restrict__ idx,float *__restrict__ out) {
    for (int i = blockIdx.x; i < b; i += gridDim.x) {
      for (int j = blockIdx.y * blockDim.x + threadIdx.x; j < m; j += blockDim.x * gridDim.y) {
        int a = idx[i * m + j];

        out[(i * m + j) * 3 + 0] = inp[(i * n + a) * 3 + 0];
        out[(i * m + j) * 3 + 1] = inp[(i * n + a) * 3 + 1];
        out[(i * m + j) * 3 + 2] = inp[(i * n + a) * 3 + 2];
      }
    }
  }

void gatherpointLauncher(int b, int n, int m, const float *inp, const int *idx, float *out) {
    gatherpointKernel<<<dim3(2, 8, 1), 512>>>(b, n, m, inp, idx, out);
}

int gatherCudaForward(at::Tensor inpTensor, at::Tensor idxTensor, at::Tensor outTensor) {
    if(inpTensor.ndimension() != 3 || inpTensor.size(2) != 3) {
        printf("GatherPoint expects (batch_size, num_points, 3) inpTensor");
        return -1;
    }

    int b = inpTensor.size(0);
    int n = inpTensor.size(1);

    if(idxTensor.ndimension() != 2 || idxTensor.size(0) != b) {
        printf("GatherPoint expects (batch_size, num_result) idxTensor");
        return -1;
    }

    int m = idxTensor.size(1);
    
    const float *inp = inpTensor.flatten().data_ptr<float>();
    int *idx = idxTensor.flatten().data_ptr<int>();
    float *out = outTensor.flatten().data_ptr<float>();
    
    gatherpointLauncher(b, n, m, inp, idx, out);

    cudaError_t err = cudaGetLastError();
    
    if (err != cudaSuccess) {
        printf("Error in nnd Output: %s\n", cudaGetErrorString(err));
        return -1;
    }

    return 1;
}

int gatherCudaBackward(at::Tensor inpTensor, at::Tensor idxTensor, at::Tensor outTensor, at::Tensor outGradTensor, at::Tensor inGradTensor) {
    if(inpTensor.ndimension() != 3 || inpTensor.size(2) != 3) {
        printf("GatherPoint expects (batch_size, num_points, 3) inpTensor");
        return -1;
    }

    int b = inpTensor.size(0);
    int n = inpTensor.size(1);
    
    if(idxTensor.ndimension() != 2 || idxTensor.size(0) != b) {
        printf("GatherPoint expects (batch_size, num_result) idxTensor");
        return -1;
    }

    int m = idxTensor.size(1);

    const float *inp = inpTensor.flatten().data_ptr<float>();
    const int *idx = idxTensor.flatten().data_ptr<int>();

    if(outGradTensor.ndimension() != 3 || outGradTensor.size(0) != b || outGradTensor.size(1) != m || outGradTensor.size(2) != 3) {
        printf("GatherPointGradGpuOp expects (batch_size,num_result,3) outGradTensor");
        return -1;
    }

    const float *out_g = outGradTensor.flatten().data_ptr<float>();
    float *inp_g = inGradTensor.flatten().data_ptr<float>();

    scatteraddpointLauncher(b, n, m, out_g, idx, inp_g);

    cudaError_t err = cudaGetLastError();
    
    if (err != cudaSuccess) {
        printf("Error in nnd Output: %s\n", cudaGetErrorString(err));
        return -1;
    }

    return 1;
}