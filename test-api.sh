export API_URL="https://diviz.knovoselov.com"
export CLIENT_ID="5tb6pekknkes6eair7o39b3hh7"

echo ""
echo "Root endpoint: "
curl -X GET "${API_URL}"

export LOGIN_URL="https://auth.diviz.knovoselov.com/login?client_id=${CLIENT_ID}&response_type=code&scope=email+openid+profile&redirect_uri=https%3A%2F%2Fdiviz.knovoselov.com%2Fauth%2Fcallback"

echo ""
echo "Login URL: ${LOGIN_URL}"

echo ""
#echo "${LOGIN_URL}"
#curl "${LOGIN_URL}"

echo ""
echo "Review endpoint (should return 401 without auth):"
curl -I -X GET "${API_URL}/review/gmeet/abc-defg-hjk"

echo ""
echo "To test with auth, first get a token:"
echo "1. Visit: ${LOGIN_URL}"
echo "2. Complete login and get token from callback"
echo "3. Test with: curl -H 'Authorization: Bearer YOUR_TOKEN' ${API_URL}/user"



echo ""
echo "logout"
curl -I -X GET "https://auth.diviz.knovoselov.com/logout?client_id=5tb6pekknkes6eair7o39b3hh7&logout_uri=https%3A%2F%2Fdiviz.knovoselov.com"
# https://us-east-2gsndrkdxe.auth.us-east-2.amazoncognito.com/login?client_id=5tb6pekknkes6eair7o39b3hh7&redirect_uri=https%3A%2F%2Fdiviz.knovoselov.com%2Fuser&response_type=code&scope=email+openid+profile