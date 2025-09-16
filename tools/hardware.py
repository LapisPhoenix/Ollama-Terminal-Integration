from cpuinfo import get_cpu_info
from psutil import cpu_count, cpu_freq, virtual_memory
from GPUtil import getGPUs


def cpu():
    """Gets information about the cpu currently. """
    cpu_name = get_cpu_info()["brand_raw"]
    cores = cpu_count(logical=False)
    threads = cpu_count(logical=True)
    cpufreq = cpu_freq()


    return f"{cpu_name} @ {cpufreq.current / 1000:.2f}Ghz (Currently) ({cpufreq.max/ 1000:.2f}Ghz Max (Advertised)- {cpufreq.min / 1000:.2f}Ghz Min (Advertised)), {cores} cores, {threads} threads"
 

def gpu():
    """Gets information about the gpu(s) currently. Only works with NVIDIA GPUs."""
    gpus = getGPUs()

    result = []
    if not gpus:
        result.append("No GPU detected.")
    else:
        for i, gpu in enumerate(gpus):
            result.append(f"\nGPU {i + 1} Information:")
            result.append(f"ID: {gpu.id}")
            result.append(f"Name: {gpu.name}")
            result.append(f"Driver: {gpu.driver}")
            result.append(f"GPU Memory Total: {gpu.memoryTotal} MB")
            result.append(f"GPU Memory Free: {gpu.memoryFree} MB")
            result.append(f"GPU Memory Used: {gpu.memoryUsed} MB")
            result.append(f"GPU Load: {gpu.load * 100}%")
            result.append(f"GPU Temperature: {gpu.temperature}°C")
    
    return '\n'.join(result)

def ram():
    """Gets infomation about the RAM currently."""
    memory_info = virtual_memory()
    
    return (
        f"Total Memory: {memory_info.total / 1073741824:.2f} GB\n"
        f"Available Memory: {memory_info.available / 1073741824:.2f} GB\n"
        f"Used Memory: {memory_info.used / 1073741824:.2f} GB\n"
        f"Memory Utilization: {memory_info.percent}%"
    )
