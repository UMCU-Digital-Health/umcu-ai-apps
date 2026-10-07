for VAR in PERSONAL_API_KEY MANIFEST_FILE_LLM_EVAL APP_ID_acc APP_ID_prod APP_NAME_acc APP_NAME_prod
do
    if [[ -z ${!VAR+x} ]]; then
        echo "env variable" $VAR "missing"
        return
    fi
done

read -p "What do you want to deploy? Options: 'ACC'/1 ; 'PROD'/2 ;" APPLICATION

APPLICATION=${APPLICATION:-N}
if [[ $APPLICATION == 'ACC' || $APPLICATION == "1" ]]; then
    echo "Deploying acceptation environment"
    cp $MANIFEST_FILE_LLM_EVAL manifest.json
    APP_ID=$APP_ID_acc
    APP_NAME=$APP_NAME_acc
elif [[ $APPLICATION == 'PROD' || $APPLICATION == "2" ]]; then
    echo "Deploying production environment"
    cp $MANIFEST_FILE_LLM_EVAL manifest.json
    APP_ID=$APP_ID_prod
    APP_NAME=$APP_NAME_prod
else
    echo "Invalid option"
    return
fi

uv export --no-hashes --no-dev -o requirements.txt

if [[ $APP_ID == '' ]]; then
    echo "New deployment selected. Not using stored APP_ID in .env."
    rsconnect deploy manifest manifest.json \
        --server https://rsc.ds.umcutrecht.nl/ \
        --new \
        --api-key "$PERSONAL_API_KEY" \
        --title "$APP_NAME" 

    echo "Please update the .env file with the new APP_ID you just created and is shown above."
else
    rsconnect deploy manifest manifest.json \
        --server https://rsc.ds.umcutrecht.nl/ \
        -i \
        --api-key "$PERSONAL_API_KEY" \
        --app-id "$APP_ID" \
        --title "$APP_NAME" 
fi 

rm manifest.json
rm requirements.txt