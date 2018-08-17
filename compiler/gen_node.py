"""Generates boilerplate code for Oniku's Node class.

Nodes in ONNX are very flexible. They allow arbitrary strings as their
operation type (e.g., "Conv") and attribute keys (e.g., "pads"). As we
would limit and expand pre-defined sets of ONNX operations and
attributes, this file will be the definition of what are supported.
"""

import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from oniku.common import codegen_util


def attr_sets(**kwargs):
    return kwargs


class Required(object):
    def __init__(self, v):
        self.v = v


class Dtype(object):
    pass


ONIKUX_GLOBAL_ATTRS = attr_sets(onikux_order=-1)

NODES = []


class NodeDef(object):

    def __init__(self, op_type, num_inputs, num_outputs, **kwargs):
        self.op_type = op_type
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.attributes = kwargs
        self.attributes.update(ONIKUX_GLOBAL_ATTRS)
        self.attr_defs = {}  # To be filled after parsed.
        NODES.append(self)


NodeDef('Neg', 1, 1)
NodeDef('Exp', 1, 1)
NodeDef('Log', 1, 1)
NodeDef('Sqrt', 1, 1)
NodeDef('Relu', 1, 1)
NodeDef('Sigmoid', 1, 1)
NodeDef('Not', 1, 1)
NodeDef('Identity', 1, 1)

NodeDef('Add', 2, 1)
NodeDef('Sub', 2, 1)
NodeDef('Mul', 2, 1)
NodeDef('Div', 2, 1)
NodeDef('Equal', 2, 1)
NodeDef('Greater', 2, 1)
NodeDef('Less', 2, 1)

NodeDef('Cast', 1, 1, to=Dtype)
NodeDef('Shape', 1, 1)
NodeDef('Reshape', 2, 1)
NodeDef('Expand', 2, 1)

NodeDef('Sum', None, 1)

NodeDef('ReduceSum', 1, 1, axes=[int], keepdims=True)
NodeDef('ReduceSumSquare', 1, 1, axes=[int], keepdims=True)
NodeDef('ReduceMean', 1, 1, axes=[int], keepdims=True)

NodeDef('Dropout', 1, (1, 2), ratio=0.5)

NodeDef('MatMul', 2, 1)
NodeDef('Gemm', 3, 1, alpha=1.0, beta=1.0, transA=False, transB=False)

conv_attrs = attr_sets(auto_pad='NOTSET',
                       dilations=[int],
                       group=1,
                       kernel_shape=[int],
                       pads=[int],
                       strides=[int])
NodeDef('Conv', (2, 3), 1, **conv_attrs)

NodeDef('BatchNormalization', 5, 1, epsilon=1e-5, momentum=0.9, spatial=1)

pool_attrs = attr_sets(auto_pad='NOTSET',
                       kernel_shape=Required([int]),
                       pads=[int],
                       storage_order=0,
                       strides=[int])
NodeDef('MaxPool', 1, (1, 2), **pool_attrs)
NodeDef('AveragePool', 1, (1, 2), count_include_pad=False, **pool_attrs)

NodeDef('Softmax', 1, 1, axis=1)
NodeDef('LogSoftmax', 1, 1, axis=1)

NodeDef('OnikuxReduceSumTo', 2, 1)


class AttrDef(object):
    def __init__(self, name, value):
        self.name = name
        self.c_name = re.sub(r'[A-Z]', lambda m: '_' + m[0].lower(), name)
        self.required = False
        self.value = None
        if isinstance(value, Required):
            self.required = True
            value = value.v
        if isinstance(value, list) or isinstance(value, type):
            self.type = value
        else:
            self.type = type(value)
            self.value = value
            assert self.type in (bool, int, str, float, Dtype)

    def c_type(self):
        if self.type == [int]:
            return 'std::vector<int>'
        return {
            bool: 'bool',
            int: 'int',
            float: 'float',
            str: 'std::string',
            Dtype: 'Dtype',
        }[self.type]

    def c_arg_type(self):
        typ = self.c_type()
        if self.type == [int] or self.type == str:
            return f'const {typ}&'
        return typ

    def onnx_type(self):
        if self.type == [int]:
            return 'onnx::AttributeProto::INTS'
        return {
            bool: 'onnx::AttributeProto::INT',
            int: 'onnx::AttributeProto::INT',
            float: 'onnx::AttributeProto::FLOAT',
            str: 'onnx::AttributeProto::STRING',
            Dtype: 'onnx::AttributeProto::INT',
        }[self.type]

    def add_func(self):
        if self.type == [int]:
            return 'add_ints_attr'
        return {
            bool: 'add_int_attr',
            int: 'add_int_attr',
            float: 'add_float_attr',
            str: 'add_str_attr',
            Dtype: 'add_dtype_attr',
        }[self.type]


ATTRS = {}

for node in NODES:
    for name, value in node.attributes.items():
        attr = AttrDef(name, value)
        node.attr_defs[name] = attr
        if name in ATTRS:
            assert attr.type == ATTRS[name].type
        else:
            ATTRS[name] = attr


ATTRS = [a for _, a in sorted(ATTRS.items())]


def gen_gen_node_base_h():
    public_lines = []
    private_lines = []
    public_lines.append('enum OpType {')
    for node in NODES:
        public_lines.append(f'k{node.op_type},')
    public_lines.append('};')
    public_lines.append('static const char* OpTypeToString(OpType op_type);')
    public_lines.append('OpType op_type() const {')
    public_lines.append('return op_type_;')
    public_lines.append('}')

    for attr in ATTRS:
        name = attr.c_name
        arg = attr.c_arg_type()
        typ = attr.c_type()

        public_lines.append(f'{arg} {name}() const ' + '{')
        public_lines.append(f'return {name}_;')
        public_lines.append('}')
        public_lines.append(f'NodeBase& set_{name}({arg} {name}) ' + '{')
        public_lines.append(f'was_{name}_set_ = true;')
        public_lines.append(f'{name}_ = {name};')
        public_lines.append('return *this;')
        public_lines.append('}')
        private_lines.append(f'{typ} {name}_;')
        private_lines.append(f'bool was_{name}_set_ = false;')

    lines = public_lines + ['protected:'] + private_lines

    with open('gen_node_base.h', 'w') as f:
        f.write(r'''// Auto-generated by gen_node.py

#pragma once

#include <string>
#include <vector>

#include <onnx/onnx.pb.h>

#include <compiler/dtype.h>

namespace oniku {

class Value;

class NodeBase {
public:
    void FillONNXAttributes(onnx::NodeProto* xnode) const;

    void SetDefaultAttributeValues();

    void ValidateNumInputsOutputs(const std::vector<Value*>& inputs, const std::vector<Value*>& outputs) const;

''')
        f.writelines(codegen_util.format_code(lines, num_indents=4))
        f.write(r'''
    OpType op_type_;
    std::vector<onnx::AttributeProto> unknown_attributes_;

    explicit NodeBase(OpType op_type);
    NodeBase(const onnx::NodeProto& xnode, const std::vector<Value*>& inputs, const std::vector<Value*>& outputs);
};

}  // namespace oniku
''')


def gen_gen_node_base_cc():
    lines = []
    lines.append('NodeBase::NodeBase(OpType op_type) : op_type_(op_type) {}')
    lines.append('NodeBase::NodeBase(const onnx::NodeProto& xnode, '
                 'const std::vector<Value*>& inputs, '
                 'const std::vector<Value*>& outputs) {')
    for i, node in enumerate(NODES):
        lines.append(f'if (xnode.op_type() == "{node.op_type}") ' + '{')
        if i:
            lines[-1] = '} else ' + lines[-1]
        lines.append(f'op_type_ = k{node.op_type};')
    lines.append('} else {')
    lines.append('CHECK(false) << "Unsupported op_type: " '
                 '<< xnode.op_type();')
    lines.append('}')

    lines.append('SetDefaultAttributeValues();')
    lines.append('ValidateNumInputsOutputs(inputs, outputs);')
    lines.append('')

    lines.append('// Validate attributes.')
    lines.append('switch (op_type_) {')
    for node in NODES:
        op = node.op_type
        lines.append(f'case k{node.op_type}: ' + '{')
        lines.append('for (const onnx::AttributeProto& xattr : '
                     'xnode.attribute()) {')
        conds = []
        bodies = []
        for _, attr in sorted(node.attr_defs.items()):
            conds.append(f'xattr.name() == "{attr.name}"')
            blines = []
            blines.append(f'CHECK_EQ(xattr.type(), {attr.onnx_type()});')
            if attr.type == int:
                blines.append(f'set_{attr.c_name}(xattr.i());')
            elif attr.type == bool:
                blines.append(f'set_{attr.c_name}(xattr.i() != 0);')
            elif attr.type == float:
                blines.append(f'set_{attr.c_name}(xattr.f());')
            elif attr.type == str:
                blines.append(f'set_{attr.c_name}(xattr.s());')
            elif attr.type == [int]:
                blines.append(f'{attr.c_name}_.assign(xattr.ints().begin(), '
                              'xattr.ints().end());')
                blines.append(f'was_{attr.c_name}_set_ = true;')
            elif attr.type == Dtype:
                blines.append(f'set_{attr.c_name}(Dtype(onnx::TensorProto::DataType(xattr.i())));')
            else:
                raise RuntimeError('Unknown attribute type: %s' % attr.type)
            bodies.append(blines)
        bodies.append('unknown_attributes_.push_back(xattr);')
        lines += codegen_util.cond(conds, bodies)

        lines.append('}')
        lines.append('}')
        lines.append('break;')
        lines.append('}')

    lines.append('}')
    lines.append('}')

    lines.append('const char* NodeBase::OpTypeToString(OpType op_type) {')
    lines.append('switch (op_type) {')
    for node in NODES:
        lines.append(f'case NodeBase::k{node.op_type}: '
                     f'return "{node.op_type}";')
    lines.append('default: CHECK(false) << "Unknown op_type: " << '
                 'static_cast<int>(op_type);')
    lines.append('}')
    lines.append('}')

    lines.append('void NodeBase::FillONNXAttributes(onnx::NodeProto* xnode) '
                 'const {')

    lines.append(r'''
    auto add_int_attr = [&xnode](const std::string& name, int v) {
        onnx::AttributeProto* xattr = xnode->add_attribute();
        xattr->set_name(name);
        xattr->set_type(onnx::AttributeProto::INT);
        xattr->set_i(v);
    };

    auto add_float_attr = [&xnode](const std::string& name, float v) {
        onnx::AttributeProto* xattr = xnode->add_attribute();
        xattr->set_name(name);
        xattr->set_type(onnx::AttributeProto::FLOAT);
        xattr->set_f(v);
    };

    auto add_str_attr = [&xnode](const std::string& name, const std::string& v) {
        onnx::AttributeProto* xattr = xnode->add_attribute();
        xattr->set_name(name);
        xattr->set_type(onnx::AttributeProto::STRING);
        xattr->set_s(v);
    };

    auto add_ints_attr = [&xnode](const std::string& name, const std::vector<int> ints) {
        if (ints.empty()) return;
        onnx::AttributeProto* xattr = xnode->add_attribute();
        xattr->set_name(name);
        xattr->set_type(onnx::AttributeProto::INTS);
        for (int s : ints) xattr->add_ints(s);
    };

    auto add_dtype_attr = [&xnode, add_int_attr](const std::string& name, Dtype v) {
        add_int_attr(name, static_cast<int>(v.ToONNX()));
    };
''')

    lines.append('switch (op_type_) {')
    for node in NODES:
        lines.append(f'case k{node.op_type}: ' + '{')
        for _, attr in sorted(node.attr_defs.items()):
            lines.append(f'if (was_{attr.c_name}_set_)')
            lines.append(f'    {attr.add_func()}("{attr.name}",'
                         f' {attr.c_name}_);')
        lines.append('break;')
        lines.append('}')
    lines.append('}')

    lines.append('for (const onnx::AttributeProto& xattr : unknown_attributes_) {')
    lines.append('*xnode->add_attribute() = xattr;')
    lines.append('}')

    lines.append('}')

    lines.append('void NodeBase::SetDefaultAttributeValues() {')
    lines.append('switch (op_type_) {')
    for node in NODES:
        lines.append(f'case k{node.op_type}: ' + '{')
        for _, attr in sorted(node.attr_defs.items()):
            if attr.value is None:
                continue
            if attr.type == str:
                lines.append(f'{attr.c_name}_ = "{attr.value}";')
            elif attr.type == bool:
                lines.append(f'{attr.c_name}_ = {str(attr.value).lower()};')
            else:
                lines.append(f'{attr.c_name}_ = {attr.value};')
        lines.append('break;')
        lines.append('}')
    lines.append('}')
    lines.append('}')

    lines.append('void NodeBase::ValidateNumInputsOutputs('
                 'const std::vector<Value*>& inputs, '
                 'const std::vector<Value*>& outputs) const {')
    lines.append('switch (op_type_) {')
    for node in NODES:
        op = node.op_type

        lines.append(f'case k{op}: ' + '{')
        for sym, num in [('inputs', node.num_inputs),
                         ('outputs', node.num_outputs)]:
            if isinstance(num, tuple):
                conds = [f'{n} == {sym}.size()' for n in num]
                cond = ' || '.join(conds)
                lines.append(f'CHECK({cond}) << '
                             f'"Unexpected number of {sym} for {op} (" << '
                             f'{sym}.size() << ")";')
            elif num is not None:
                lines.append(f'CHECK_EQ({num}, {sym}.size()) << '
                             f'"Unexpected number of {sym} for {op}";')

        lines.append('break;')
        lines.append('}')
    lines.append('}')
    lines.append('}')

    with open('gen_node_base.cc', 'w') as f:
        f.write(r'''// Auto-generated by gen_node.py

#include "gen_node_base.h"

#include <string>
#include <vector>

#include <onnx/onnx.pb.h>

#include <common/log.h>

namespace oniku {

''')
        f.writelines(codegen_util.format_code(lines))
        f.write(r'''

}  // namespace oniku
''')


gen_gen_node_base_h()
gen_gen_node_base_cc()