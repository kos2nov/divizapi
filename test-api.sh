export API_URL="https://diviz.knovoselov.com/api"
export CLIENT_ID="5tb6pekknkes6eair7o39b3hh7"

echo ""
echo "Root endpoint: "
curl -X GET "${API_URL}"

export LOGIN_URL="https://auth.diviz.knovoselov.com/login?client_id=${CLIENT_ID}&response_type=code&scope=email+openid+profile&redirect_uri=https%3A%2F%2Fdiviz.knovoselov.com%2Fauth%2Fcallback"

echo ""
echo "Login URL: ${LOGIN_URL}"
#curl "${LOGIN_URL}"

echo ""
echo "Review endpoint (should return 401 without auth):"
curl -I -X GET "${API_URL}/review/gmeet/abc-defg-hjk"

echo ""
echo "To test with auth, first get a token:"
echo "1. Visit: ${LOGIN_URL}"
echo "2. Complete login and get token from callback"
echo "3. Test with: curl -H 'Authorization: Bearer ACCESS_TOKEN' ${API_URL}/user"

export ACCESS_TOKEN="eyJraWQiOiIrZlNcL0lhTmIybmtObTdyS3QybHRKR1dsMHFCQmN6MXI4enBwY1o3clRQZz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJlMTliNzU5MC1lMDAxLTcwZjctYzU2ZS1jNzYyMTg2MDJhNmIiLCJjb2duaXRvOmdyb3VwcyI6WyJ1cy1lYXN0LTJfR1NOZHJLRFhFX0dvb2dsZSJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0yLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMl9HU05kcktEWEUiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiI1dGI2cGVra25rZXM2ZWFpcjdvMzliM2hoNyIsIm9yaWdpbl9qdGkiOiJiYzJkZmI2NC0zNzdlLTQyMzgtYjE5NS1hYzg3OTQ3MTU5YTUiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiYXV0aF90aW1lIjoxNzU2OTI2NTE0LCJleHAiOjE3NTY5MzAxMTQsImlhdCI6MTc1NjkyNjUxNCwianRpIjoiMDU5Zjk1NmYtMzRiYi00OWU3LTk2YzYtNzNhN2FhMmY2ZmViIiwidXNlcm5hbWUiOiJnb29nbGVfMTExMDE3NzQ2MjgzMTI3NTIzODkxIn0.HyMejMgpZBI6wtSu5996pHpBMgImA0n773_gwzjOg8GEexlQZkwuuST3-4VZf3YpGHqo56SntFBDK2gWnTzPEDf6pLzvgXGQZupW7DsCYY32INxw4wOzYc4EV37C9Aw0-dtWup87mP6DrfUOtaLrxH7fdzr6qpsHBflDwcrCz4FpwYGwl244scZpLWDz0IXMnQ1zIS1T1RFMbCJo1_2GziJt9P1DeP1-Y9C8U1Wq3tKwbCSUGV2GenSutgfkun0W6Kw-5kyTaehOUyCj-2NHjQUJRkBhZSzhsIjYlhULcvoEvjrannK8vcX2rdGjFbdVUUDwPgqkj1WmD3cy0Qa4hA"

curl -X GET -H "Authorization: Bearer ${ACCESS_TOKEN}" ${API_URL}/user


#echo ""
#echo "logout"
# curl -I -X GET "https://auth.diviz.knovoselov.com/logout?client_id=5tb6pekknkes6eair7o39b3hh7&logout_uri=https%3A%2F%2Fdiviz.knovoselov.com"
