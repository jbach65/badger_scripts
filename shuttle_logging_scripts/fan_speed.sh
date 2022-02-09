echo "epoch_time" | tr '\n' ',';
sensors | grep "fan" | awk '{print $1}' | sed -e ':a' -e 'N;$!ba' -e 's/\n/,/g' | tr -d : | tr '\n' ',';
echo ""

while :
do
    date +%s | tr '\n' ',';
    sensors | grep "fan" | awk '{print $2}' | sed -e ':a' -e 'N;$!ba' -e 's/\n/,/g' | tr '\n' ',';
    echo ""
    sleep 1;
done
