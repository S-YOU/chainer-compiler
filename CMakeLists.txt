cmake_minimum_required(VERSION 3.4)

if(POLICY CMP0077)
  cmake_policy(SET CMP0077 NEW)
endif()

execute_process(COMMAND git submodule update --init)

include(cmake/third-party.cmake)

SET(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake ${CMAKE_MODULE_PATH})

if(DEFINED ENV{CHAINER_COMPILER_BUILD_CUDA})
    set(DEFAULT_CHAINER_COMPILER_BUILD_CUDA $ENV{CHAINER_COMPILER_BUILD_CUDA})
else()
    set(DEFAULT_CHAINER_COMPILER_BUILD_CUDA OFF)
endif()
option(CHAINER_COMPILER_BUILD_CUDA "Build CUDA backend (if CUDA is available)" ${DEFAULT_CHAINER_COMPILER_BUILD_CUDA})

if(DEFINED ENV{CHAINER_COMPILER_ENABLE_CUDNN})
    set(DEFAULT_CHAINER_COMPILER_ENABLE_CUDNN $ENV{CHAINER_COMPILER_ENABLE_CUDNN})
else()
    set(DEFAULT_CHAINER_COMPILER_ENABLE_CUDNN OFF)
endif()
option(CHAINER_COMPILER_ENABLE_CUDNN "Enable CUDNN" ${DEFAULT_CHAINER_COMPILER_ENABLE_CUDNN})

if(DEFINED ENV{CHAINER_COMPILER_ENABLE_NVTX})
    set(DEFAULT_CHAINER_COMPILER_ENABLE_NVTX $ENV{CHAINER_COMPILER_ENABLE_NVTX})
else()
    set(DEFAULT_CHAINER_COMPILER_ENABLE_NVTX OFF)
endif()
option(CHAINER_COMPILER_ENABLE_NVTX "Enable NVTX" ${DEFAULT_CHAINER_COMPILER_ENABLE_NVTX})

if(DEFINED ENV{CHAINER_COMPILER_ENABLE_NVRTC})
    set(DEFAULT_CHAINER_COMPILER_ENABLE_NVRTC $ENV{CHAINER_COMPILER_ENABLE_NVRTC})
else()
    set(DEFAULT_CHAINER_COMPILER_ENABLE_NVRTC OFF)
endif()
option(CHAINER_COMPILER_ENABLE_NVRTC "Enable NVRTC" ${DEFAULT_CHAINER_COMPILER_ENABLE_NVRTC})

if(DEFINED ENV{CHAINER_COMPILER_ENABLE_OPENCV})
    set(DEFAULT_CHAINER_COMPILER_ENABLE_OPENCV $ENV{CHAINER_COMPILER_ENABLE_OPENCV})
else()
    set(DEFAULT_CHAINER_COMPILER_ENABLE_OPENCV OFF)
endif()
option(CHAINER_COMPILER_ENABLE_OPENCV "Enable OPENCV" ${DEFAULT_CHAINER_COMPILER_ENABLE_OPENCV})

if(DEFINED ENV{CHAINER_COMPILER_ENABLE_PYTHON})
    set(DEFAULT_CHAINER_COMPILER_ENABLE_PYTHON $ENV{CHAINER_COMPILER_ENABLE_PYTHON})
else()
    set(DEFAULT_CHAINER_COMPILER_ENABLE_PYTHON OFF)
endif()
option(CHAINER_COMPILER_ENABLE_PYTHON "Enable PYTHON" ${DEFAULT_CHAINER_COMPILER_ENABLE_PYTHON})

if(DEFINED ENV{CHAINER_COMPILER_ENABLE_TVM})
    set(DEFAULT_CHAINER_COMPILER_ENABLE_TVM $ENV{CHAINER_COMPILER_ENABLE_TVM})
else()
    set(DEFAULT_CHAINER_COMPILER_ENABLE_TVM OFF)
endif()
option(CHAINER_COMPILER_ENABLE_TVM "Enable TVM" ${DEFAULT_CHAINER_COMPILER_ENABLE_TVM})

option(CHAINER_COMPILER_NGRAPH_DIR "The path to ngraph_dist" OFF)

option(CHAINER_COMPILER_BUILD_TESTS "Build C++ tests" ON)
option(CHAINER_COMPILER_GENERATE_TESTS "Generate tests for scripts/runtests.py" ON)

if(${CHAINER_COMPILER_GENERATE_TESTS})
  set(CHAINER_COMPILER_TEST_ALL ALL)
else()
  set(CHAINER_COMPILER_TEST_ALL "")
endif()

set(ONNX_ML ON)
set(ONNX_NAMESPACE "chainer_compiler_onnx")
add_subdirectory(third_party/onnx)
add_custom_target(onnx_files
  DEPENDS
  ${CMAKE_CURRENT_BINARY_DIR}/third_party/onnx/onnx/onnx_chainer_compiler_onnx-ml.pb.h
  )
# It seems `onnx` target compiles onnx*.pb.cc. As this will let other
# files produce warnings, we suppress all warnings from ONNX by -w.
target_compile_definitions(onnx PRIVATE ONNX_API=)
target_compile_options(onnx PRIVATE -w)

if (${CHAINER_COMPILER_ENABLE_PYTHON})
  set(CHAINERX_BUILD_PYTHON ON)
endif()

add_subdirectory(third_party/chainer/chainerx_cc)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/third_party/chainer/chainerx_cc)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/third_party/chainer/chainerx_cc/gsl-lite/include)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/third_party/chainer/chainerx_cc/optional-lite/include)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/third_party/chainer/chainerx_cc/googletest-src/googletest/include)

enable_testing()

add_definitions(-DONNX_ML=1)
add_definitions(-DONNX_NAMESPACE=${ONNX_NAMESPACE})

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=native")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -W")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-trigraphs")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-sign-compare")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-unused-parameter")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++14")

# OpenCV
if(${CHAINER_COMPILER_ENABLE_OPENCV})
  find_package(OpenCV REQUIRED)
endif()

if(POLICY ${CMP0077})
  # Make both chainer-compiler and ChainerX consistent.
  set(CHAINERX_BUILD_CUDA ${CHAINER_COMPILER_BUILD_CUDA})
else()
  if(${CHAINER_COMPILER_BUILD_CUDA})
    if(NOT ${CHAINERX_BUILD_CUDA})
      message(FATAL_ERROR "Please set -DCHAINERX_BUILD_CUDA=ON when -DCHAINER_COMPILER_ENABLE_CUDA is ON")
    endif()
  else()
    if(${CHAINERX_BUILD_CUDA})
      message(FATAL_ERROR "Please set -DCHAINERX_BUILD_CUDA=OFF when -DCHAINER_COMPILER_ENABLE_CUDA is OFF")
    endif()
  endif()
endif()

# CUDA
if(${CHAINER_COMPILER_BUILD_CUDA})
  find_package(CUDA REQUIRED)
  if(${CUDA_FOUND})
    add_definitions(-DCHAINER_COMPILER_ENABLE_CUDA=1)
    set(CHAINER_COMPILER_CUDA_LIBRARIES ${CUDA_CUDART_LIBRARY})

    if(${CHAINER_COMPILER_ENABLE_CUDNN})
      add_definitions(-DCHAINER_COMPILER_ENABLE_CUDNN=1)
      find_package(CuDNN 7 REQUIRED)
      include_directories(${CUDNN_INCLUDE_DIRS})
      link_directories(${CUDNN_LIBRARY_DIRS})
      set(CHAINER_COMPILER_CUDA_LIBRARIES ${CHAINER_COMPILER_CUDA_LIBRARIES} ${CUDNN_LIBRARIES})
    endif()

    if(${CHAINER_COMPILER_ENABLE_NVRTC})
      add_definitions(-DCHAINER_COMPILER_ENABLE_NVRTC=1)
      link_directories(${CUDA_TOOLKIT_ROOT_DIR}/lib64)
      set(CHAINER_COMPILER_CUDA_LIBRARIES ${CHAINER_COMPILER_CUDA_LIBRARIES} cuda nvrtc)
    endif()

    if(${CHAINER_COMPILER_ENABLE_NVTX})
      add_definitions(-DCHAINER_COMPILER_ENABLE_NVTX=1)
      link_directories(${CUDA_TOOLKIT_ROOT_DIR}/lib64)
      set(CHAINER_COMPILER_CUDA_LIBRARIES ${CHAINER_COMPILER_CUDA_LIBRARIES} nvToolsExt)
    endif()

  endif()
endif()

if(NOT ("${CHAINER_COMPILER_NGRAPH_DIR}" STREQUAL "OFF"))
  add_definitions(-DCHAINER_COMPILER_ENABLE_NGRAPH=1)
  set(CHAINER_COMPILER_NGRAPH_INCLUDE_DIRS ${CHAINER_COMPILER_NGRAPH_DIR}/include)
  set(CHAINER_COMPILER_NGRAPH_LINK_DIRS ${CHAINER_COMPILER_NGRAPH_DIR}/lib)
  set(CHAINER_COMPILER_NGRAPH_LIBRARIES ngraph)
  link_directories(AFTER ${CHAINER_COMPILER_NGRAPH_LINK_DIRS})
endif()

if(${CHAINER_COMPILER_ENABLE_TVM})
  add_definitions(-DCHAINER_COMPILER_ENABLE_TVM=1)
  set(CHAINER_COMPILER_TVM_INCLUDE_DIRS ${CHAINER_COMPILER_TVM_INCLUDE_DIRS} /usr/local/include/HalideIR)
  set(CHAINER_COMPILER_TVM_LIBRARIES tvm)
  set(CHAINER_COMPILER_TVM_RUNTIME_LIBRARIES tvm_runtime)
endif()

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/third_party/onnx ${CMAKE_CURRENT_BINARY_DIR}/third_party/onnx)

add_custom_target(large_tests)

if (${CHAINER_COMPILER_ENABLE_PYTHON})
  include_directories(${CMAKE_BINARY_DIR}/third_party/chainer/chainerx_cc/pybind11/include)
  add_subdirectory(python)
endif()

add_subdirectory(compiler)
add_subdirectory(common)
add_subdirectory(feeder)
add_subdirectory(runtime)
add_subdirectory(scripts)
add_subdirectory(tools)

set(CH2O_FILES
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/__init__.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/builtin_funcs.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/callable.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/chainer2onnx.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/funcs.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/initializer.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/links.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/test_args.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/testcasegen.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/utils.py
  ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/ch2o/value.py
  )

function(gen_ch2o_test dir ch2o_test all)

  set(ch2o_test_py ${CMAKE_CURRENT_SOURCE_DIR}/ch2o/tests/${dir}/${ch2o_test}.py)
  set(out_dir ${CMAKE_CURRENT_SOURCE_DIR}/out/ch2o_${dir}_${ch2o_test}) # TODO: move to build/ directory
  set(out_stamp ${CMAKE_CURRENT_BINARY_DIR}/stamp_out/ch2o_${dir}_${ch2o_test})

  file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/stamp_out)

  add_custom_command(
    OUTPUT ${out_stamp}
    COMMAND PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/ch2o python3 ${ch2o_test_py} ${out_dir} --quiet && touch ${out_stamp}
    MAIN_DEPENDENCY ${ch2o_test_py}
    DEPENDS ${CH2O_FILES}
    )

  add_custom_target(
    ${dir}_${ch2o_test}
    ${all}
    DEPENDS ${out_stamp})

  add_dependencies(large_tests ${dir}_${ch2o_test})

endfunction()

foreach(
    ch2o_test
    Cmp
    For
    ForAndIf
    If
    LinkInFor
    ListComp
    MultiClass
    MultiFunction
    Range
    Sequence
    Slice
    UserDefinedFunc
    )

  gen_ch2o_test(syntax ${ch2o_test} "${CHAINER_COMPILER_TEST_ALL}")

endforeach()

foreach(
    ch2o_test
    AddMul
    AveragePool2d
    BatchNorm
    BroadcastTo
    Ceil
    Concat
    Convolution2D
    Cumsum
    Dropout
    EmbedID
    ExpandDims
    Hstack
    Id
    LRN
    Len
    Linear
    Matmul
    MaxPool2d
    Mean
    NStepBiLSTM
    NStepLSTM
    NpArray
    NpFull
    NpZeros
    PadSequence
    Relu
    Reshape
    ResizeImages
    Roi
    Separate
    Shape
    Sigmoid
    Size
    SplitAxis
    Squeeze
    Softmax
    SoftmaxClossEntropy
    Stack
    Sum
    SwapAxes
    Tanh
    Unpooling2D
    Variable
    Vstack
    )

  gen_ch2o_test(node ${ch2o_test} "${CHAINER_COMPILER_TEST_ALL}")

endforeach()

foreach(
    ch2o_test
    EspNet_AttDot
    EspNet_AttLoc
    EspNet_BLSTM
    EspNet_Decoder
    EspNet_E2E
    EspNet_VGG2L
    MLP_with_loss
    MyLSTM
    StatelessLSTM

    Resnet_with_loss  # Will not be tested by runtests.py, though.
    )

  gen_ch2o_test(model ${ch2o_test} "${CHAINER_COMPILER_TEST_ALL}")

endforeach()

foreach(
    ch2o_test
    Alex_with_loss
    GoogleNet_with_loss
    )

  gen_ch2o_test(model ${ch2o_test} "")

endforeach()

set(ELICHIKA_FILES
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/__init__.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/chainer2onnx.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/__init__.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/config.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/core.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/functions.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/functions_builtin.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/graphs.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/nodes.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/utils.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/values.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/values_builtin.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/veval_bin.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/veval_unary.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/vevaluator.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/elichika/parser/visualizer.py

  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/testtools/__init__.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/testtools/initializer.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/testtools/test_args.py
  ${CMAKE_CURRENT_SOURCE_DIR}/elichika/testtools/testcasegen.py
  )

# Include elichika_tests so the build file will be regenerated when a
# new test is added.
include(scripts/elichika_tests.py)

function(gen_elichika_test dir all)
  set(elichika_tests_py ${CMAKE_CURRENT_SOURCE_DIR}/scripts/elichika_tests.py)
  set(out_stamp ${CMAKE_CURRENT_BINARY_DIR}/stamp_out/elichika_${dir})

  execute_process(
    COMMAND ${elichika_tests_py} --list ${dir}
    OUTPUT_VARIABLE test_files
    )

  file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/stamp_out)

  add_custom_command(
    OUTPUT ${out_stamp}
    COMMAND PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/elichika python3 ${elichika_tests_py} --generate ${dir} && touch ${out_stamp}
    DEPENDS ${elichika_tests_py} ${test_files}
    )

  message(${out_stamp})

  add_custom_target(
    gen_elichika_${dir}
    ${all}
    DEPENDS ${out_stamp})

  add_dependencies(large_tests gen_elichika_${dir})

endfunction()

gen_elichika_test(node "${CHAINER_COMPILER_TEST_ALL}")
gen_elichika_test(syntax "${CHAINER_COMPILER_TEST_ALL}")
