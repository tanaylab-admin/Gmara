
for IGNORED in genes/*/namespaces/sources/*.Ignored.txt
do
    echo "IGNORED: $IGNORED"
    MISSING=`echo $IGNORED | sed 's/Ignored/Missing/'`
    echo "MISSINF: $MISSING"
    if [ -f $IGNORED ]
    then
        cat $IGNORED >> $MISSING
        rm $IGNORED
    fi
done
