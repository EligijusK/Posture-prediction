#include <ATen/cuda/CUDAContext.h>
#include <torch/extension.h>

#include <stdio.h>
#include <ATen/ATen.h>

#include <cuda.h>
#include <cuda_runtime.h>

void farthestpointsamplingLauncher(int b, int n, int m, const float *inp, float *temp, int *out);
__global__ void farthestpointsamplingKernel(int b, int n, int m, const float *__restrict__ dataset, float *__restrict__ temp, int *__restrict__ idxs);

__global__ void farthestpointsamplingKernel(int b, int n, int m, const float *__restrict__ dataset, float *__restrict__ temp, int *__restrict__ idxs) {
    if (m <= 0) return;

    const int BlockSize = 512;
    
    __shared__ float dists[BlockSize];
    __shared__ int dists_i[BlockSize];
    
    const int BufferSize = 3072;
    __shared__ float buf[BufferSize * 3];
    
    for (int i = blockIdx.x; i < b; i += gridDim.x) {
        int old = 0;

        if (threadIdx.x == 0) idxs[i * m + 0] = old;
        
        for (int j = threadIdx.x; j < n; j += blockDim.x) {
            temp[blockIdx.x * n + j] = 1e38;
        }

        for (int j = threadIdx.x; j < min(BufferSize, n) * 3; j += blockDim.x) {
            buf[j] = dataset[i * n * 3 + j];
        }
        __syncthreads();

        for (int j = 1; j < m; j++) {
            int besti = 0;
            float best = -1;

            float x1 = dataset[i * n * 3 + old * 3 + 0];
            float y1 = dataset[i * n * 3 + old * 3 + 1];
            float z1 = dataset[i * n * 3 + old * 3 + 2];

            for (int k = threadIdx.x; k < n; k += blockDim.x) {
                float td = temp[blockIdx.x*n+k];
                float x2, y2, z2;

                if (k < BufferSize){
                    x2 = buf[k * 3 + 0];
                    y2 = buf[k * 3 + 1];
                    z2 = buf[k * 3 + 2];
                } else {
                    x2=dataset[i * n * 3 + k * 3 + 0];
                    y2=dataset[i * n * 3 + k * 3 + 1];
                    z2=dataset[i * n * 3 + k * 3 + 2];
                }
               
                float d = (x2-x1) * (x2-x1) + (y2-y1) * (y2-y1) + (z2-z1) * (z2-z1);
                float d2 = min(d, td);

                if (d2 != td) temp[blockIdx.x * n + k] = d2;
                
                if (d2 > best){
                    best = d2;
                    besti = k;
                }
            }

            dists[threadIdx.x] = best;
            dists_i[threadIdx.x] = besti;

            for (int u = 0; (1 << u)< blockDim.x; u++){
                __syncthreads();

                if (threadIdx.x<(blockDim.x >> (u + 1))) {
                    int i1 = (threadIdx.x * 2) << u;
                    int i2 = (threadIdx.x * 2 + 1) << u;

                    if (dists[i1] < dists[i2]) {
                        dists[i1] = dists[i2];
                        dists_i[i1] = dists_i[i2];
                    }
                }
            }
            __syncthreads();

            old = dists_i[0];

            if (threadIdx.x == 0) idxs[i * m + j] = old;
        }
    }
}

//require 32*n working space
void farthestpointsamplingLauncher(int b, int n, int m, const float *inp, float *temp, int *out) {
    farthestpointsamplingKernel<<<32,512>>>(b, n, m, inp, temp, out);
}

int farthestPointSamplingCuda(const int nsamples, at::Tensor inpTensor, at::Tensor outTensor) {
    if(inpTensor.ndimension() != 3 || inpTensor.size(2) != 3) {
        printf("FarthestPointSample expects (batch_size, num_points, 3) inp shape.");
        return -1;
    }
    
    int m = nsamples;
    int b = inpTensor.size(0);
    int n = inpTensor.size(1);

    const float *inp = inpTensor.flatten().data_ptr<float>();
    int *out = outTensor.flatten().data_ptr<int>();

    auto options = torch::TensorOptions()
        .device(inpTensor.device().type(), inpTensor.device().index())
        .dtype(torch::kFloat32)
        .requires_grad(false);
    at::Tensor tempTensor = torch::empty({32, n}, options);

    float *temp = tempTensor.flatten().data_ptr<float>();

    farthestpointsamplingLauncher(b, n, m, inp, temp, out);

    cudaError_t err = cudaGetLastError();
    
    if (err != cudaSuccess) {
        printf("Error in nnd Output: %s\n", cudaGetErrorString(err));
        return -1;
    }

    return 1;
}