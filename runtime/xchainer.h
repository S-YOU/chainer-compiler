#pragma once

#include <map>
#include <string>

#include <onnx/onnx.pb.h>

#include <xchainer/array.h>

namespace oniku {
namespace runtime {

typedef std::map<std::string, xchainer::Array> InOuts;

InOuts RunGraph(const InOuts& inputs, bool use_trace);

xchainer::Array GetOrDie(const InOuts& m, std::string name);
void SetOrDie(InOuts& m, std::string name, xchainer::Array a);

// TODO(hamaji): Investigate xChainer's BatchNorm.
xchainer::Array BatchNormONNX(
        xchainer::Array x, xchainer::Array s, xchainer::Array bias, xchainer::Array mean, xchainer::Array var, float epsilon);

xchainer::Shape ArrayToShape(const xchainer::Array a);

xchainer::Array MakeArrayFromONNX(const onnx::TensorProto& xtensor);

}  // namespace runtime
}  // namespace oniku