import time
import functools


# 1. 定义一个计时器装饰器
def timer_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # 使用高精度计时器
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(
            f"函数 {func.__name__}({args[0]}) 运行耗时: {end_time - start_time:.8f} 秒"
        )
        return result

    return wrapper


# 2. 递归计算斐波那契数
# 使用 lru_cache 装饰器可以极大提高递归效率（可选）
# @functools.lru_cache(None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


# 3. 包装一层带计时的函数，避免递归内部反复打印计时
@timer_decorator
def get_fib_with_timer(n):
    return fibonacci(n)


# --- 测试运行 ---
if __name__ == "__main__":
    number = int(input("Give me a number: "))  # 注意：纯递归下超过 35 会显著变慢
    print(f"开始计算第 {number} 个斐波那契数...")
    res = get_fib_with_timer(number)
    print(f"计算结果为: {res}")
