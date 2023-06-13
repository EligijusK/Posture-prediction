#include <torch/extension.h>
#include <vector>

int farthestPointSamplingCuda(int nsamples, at::Tensor t_in, at::Tensor t_out);
int farthestPointSampling(int nsamples, at::Tensor t_in, at::Tensor t_out) {
    return farthestPointSamplingCuda(nsamples, t_in, t_out);
}

int gatherCudaForward(at::Tensor t_in, at::Tensor t_idx, at::Tensor t_out);
int gatherForward(at::Tensor t_in, at::Tensor t_idx, at::Tensor t_out) {
    return gatherCudaForward(t_in, t_idx, t_out);
}

int gatherCudaBackward(at::Tensor t_in, at::Tensor t_idx, at::Tensor t_out, at::Tensor t_out_grad, at::Tensor t_in_grad);
int gatherBackward(at::Tensor t_in, at::Tensor t_idx, at::Tensor t_out, at::Tensor t_out_grad, at::Tensor t_in_grad) {
    return gatherCudaBackward(t_in, t_idx, t_out, t_out_grad, t_in_grad);
}


PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("farhest_point_sampling", &farthestPointSampling, "FPS (CUDA)");
  m.def("gather_forward", &gatherForward, "Gather Forward (CUDA)");
  m.def("gather_backward", &gatherBackward, "Gather Bacward (CUDA)");
}