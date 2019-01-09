#include "xcvm.h"

#include <numeric>

#ifdef ONIKU_ENABLE_NVTX
#include <nvToolsExt.h>
#endif  // ONIKU_ENABLE_NVTX

#include <chainerx/array.h>

#include <common/strutil.h>
#include <runtime/chrome_tracing.h>
#include <runtime/meminfo.h>
#include <runtime/xchainer.h>
#include <runtime/xcvm.pb.h>
#include <runtime/xcvm_op.h>
#include <runtime/xcvm_state.h>

#define RANGE(x) (x).begin(), (x).end()

namespace oniku {
namespace runtime {

XCVMOptions::XCVMOptions() {
    int num_ops = 1;
    while (XCInstructionProto::Op_IsValid(num_ops)) {
        ++num_ops;
    }
    verbose_ops.resize(num_ops);
}

XCVM::XCVM(const XCProgramProto& program) {
    num_variables_ = 0;
    for (const XCInstructionProto& inst : program.instructions()) {
        for (int output : inst.outputs()) {
            num_variables_ = std::max(num_variables_, output + 1);
        }
    }

    for (const XCInstructionProto& inst : program.instructions()) {
        XCVMOp* op = MakeXCVMOp(inst);
        program_.emplace_back(op);
    }
}

XCVM::~XCVM() {
}

InOuts XCVM::Run(const InOuts& program_inputs, const XCVMOptions& options) {
    XCVMState state(options, num_variables_, program_inputs);
    Run(&state);
    return state.GetOutputs();
}

void XCVM::Run(XCVMState* state) {
    state->SetProgram(&program_);
    const XCVMOptions& options = state->options();
    int64_t peak_usage = 0;

    while (true) {
        int pc = state->pc();
        if (pc >= program_.size()) break;

        XCVMOp* op = program_[pc].get();

        {
            ChromeTracingEmitter::ScopedEvent se(options.chrome_tracing, "XCVM", op->name(), pc);
#ifdef ONIKU_ENABLE_NVTX
            nvtxRangePush(op->name().c_str());
#endif
            try {
                op->Run(state);
            } catch (...) {
                std::cerr << "Exception in " << op->debug_info() << std::endl;
                throw;
            }
#ifdef ONIKU_ENABLE_NVTX
            nvtxRangePop();
#endif
        }

        state->set_pc(state->pc() + 1);

        if (options.dump_memory_usage && options.base_memory_usage >= 0) {
            int64_t bytes = options.base_memory_usage - GetMemoryUsageInBytes();
            int64_t mbs = bytes / 1000 / 1000;
            peak_usage = std::max(mbs, peak_usage);
            std::cerr << " Memory usage: " << mbs << "MB" << std::endl;
        }
    }

    if (options.dump_memory_usage) {
        state->ShowVariableStatus();
        std::cerr << "Peak memory usage: " << peak_usage << "MB" << std::endl;
    }
}

}  // namespace runtime
}  // namespace oniku
