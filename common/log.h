#pragma once

#include <sstream>
#include <string>

namespace chainer_compiler {

class FailMessageStream {
public:
    FailMessageStream(const std::string msg, const char* func, const char* file, int line, bool is_check = true);

    ~FailMessageStream();

    template <class T>
    FailMessageStream& operator<<(const T& v) {
        oss_ << v;
        return *this;
    }

private:
    std::ostringstream oss_;
    const std::string msg_;
    const char* func_;
    const char* file_;
    const int line_;
    const bool is_check_;
};

#define QFAIL() chainer_compiler::FailMessageStream("", __func__, __FILE__, __LINE__, false)

#define CHECK(cond) \
    while (!(cond)) chainer_compiler::FailMessageStream("Check `" #cond "' failed!", __func__, __FILE__, __LINE__)

#define CHECK_CMP(a, b, op)                                                                                      \
    while (!((a)op(b)))                                                                                          \
    chainer_compiler::FailMessageStream("Check `" #a "' " #op " `" #b "' failed!", __func__, __FILE__, __LINE__) \
            << "(" << (a) << " vs " << (b) << ") "

#define CHECK_EQ(a, b) CHECK_CMP(a, b, ==)
#define CHECK_NE(a, b) CHECK_CMP(a, b, !=)
#define CHECK_LT(a, b) CHECK_CMP(a, b, <)
#define CHECK_LE(a, b) CHECK_CMP(a, b, <=)
#define CHECK_GT(a, b) CHECK_CMP(a, b, >)
#define CHECK_GE(a, b) CHECK_CMP(a, b, >=)

#ifdef NDEBUG
#define DCHECK(cond)
#define DCHECK_EQ(a, b)
#define DCHECK_NE(a, b)
#define DCHECK_LT(a, b)
#define DCHECK_LE(a, b)
#define DCHECK_GT(a, b)
#define DCHECK_GE(a, b)
#else
#define DCHECK(cond) CHECK(cond)
#define DCHECK_EQ(a, b) CHECK_EQ(a, b)
#define DCHECK_NE(a, b) CHECK_NE(a, b)
#define DCHECK_LT(a, b) CHECK_LT(a, b)
#define DCHECK_LE(a, b) CHECK_LE(a, b)
#define DCHECK_GT(a, b) CHECK_GT(a, b)
#define DCHECK_GE(a, b) CHECK_GE(a, b)
#endif

#define WARN_ONCE(msg)                                                        \
    do {                                                                      \
        static bool logged_##__LINE__ = false;                                \
        if (!logged_##__LINE__) std::cerr << "WARNING: " << msg << std::endl; \
        logged_##__LINE__ = true;                                             \
    } while (0)

}  // namespace chainer_compiler
