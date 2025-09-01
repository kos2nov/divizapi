export API_URL="https://aqqlkawmgc.execute-api.us-east-2.amazonaws.com/prod"

echo ""
echo "Root endpoint: "
curl -X GET "${API_URL}"

export LOGIN_URL="https://us-east-2gsndrkdxe.auth.us-east-2.amazoncognito.com/login?client_id=5tb6pekknkes6eair7o39b3hh7&response_type=code&scope=email+openid+profile&redirect_uri=${API_URL}/user"

echo ""
echo "${LOGIN_URL}"
curl "${LOGIN_URL}"

echo ""
echo "Review endpoint:"
curl -I -X GET "${API_URL}/review/gmeet/abc-defg-hjk"

