echo "epoch_time" | tr '\n' ',';
sensors | grep " id" | awk '{print $1 $2}' | tr -d : | tr '\n' ',';
sensors | grep "Core" | awk '{print $1 $2}' | sed -e ':a' -e 'N;$!ba' -e 's/\n/,/g' | tr -d :

while :
do
    date +%s | tr '\n' ',';
    sensors | grep " id" | awk '{print $4}' | tr -d +°C | sed -e ':a' -e 'N;$!ba' -e 's/\n/,/g' | tr '\n' ',';
    sensors | grep Core | awk '{print $3}' | tr -d +°C | sed -e ':a' -e 'N;$!ba' -e 's/\n/,/g'
    sleep 1;
done
