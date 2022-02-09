echo "epoch_time" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu0" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu1" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu2" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu3" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu4" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu5" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu6" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu7" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu8" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu9" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu10" | tr '\n' ',';
ls /sys/devices/system/cpu/ | grep -w "cpu11" | tr '\n' ',';
echo "cpu0_min_freq, cpu0_max_freq"

while :
do
    date +%s | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu1/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu3/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu4/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu5/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu6/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu7/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu8/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu9/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu10/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu11/cpufreq/scaling_cur_freq 2>/dev/null | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq | tr '\n' ',';
    cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq;
    sleep .95;
done
