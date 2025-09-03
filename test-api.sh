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

export ACCESS_TOKEN="eyJraWQiOiJyZW5laHBEZmh0TW5FS0V5akNocTlOMmIrMHlXZEtJbUxNWFFxQnhETUdJPSIsImFsZyI6IlJTMjU2In0.eyJhdF9oYXNoIjoiaWN0eGN3WU1uQzZPYTBDZ09ZYWdOQSIsInN1YiI6ImUxOWI3NTkwLWUwMDEtNzBmNy1jNTZlLWM3NjIxODYwMmE2YiIsImNvZ25pdG86Z3JvdXBzIjpbInVzLWVhc3QtMl9HU05kcktEWEVfR29vZ2xlIl0sImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMi5hbWF6b25hd3MuY29tXC91cy1lYXN0LTJfR1NOZHJLRFhFIiwiY29nbml0bzp1c2VybmFtZSI6Imdvb2dsZV8xMTEwMTc3NDYyODMxMjc1MjM4OTEiLCJub25jZSI6InFSaVgtZFZVM21kOVNFWHFCaklraFA4TzlkUUp1ZUVUOVVHRkl5TDFiaXpIeE8zRm1fZEloZHRtckhOTG1XTlpaNjAyb0x5OUJhZnRMd051eHpGU0NJMnBoUzBaN0kyNF9MV0ZNWDRnNDdVQlpVRWVmWEM0ZjFoNGVkNEJLZ3FXT19LOEJHcGxUalJqenlxMXZkcWhueGxhNVpITDJETHJVd0JWUnhLaG5vSSIsIm9yaWdpbl9qdGkiOiJmODFkMjU5Yi01Y2U4LTQyZTItYjBiMi1hN2NjYmM0ZjFlYzciLCJhdWQiOiI1dGI2cGVra25rZXM2ZWFpcjdvMzliM2hoNyIsImlkZW50aXRpZXMiOlt7ImRhdGVDcmVhdGVkIjoiMTc1Njc3MjY4NjA3MyIsInVzZXJJZCI6IjExMTAxNzc0NjI4MzEyNzUyMzg5MSIsInByb3ZpZGVyTmFtZSI6Ikdvb2dsZSIsInByb3ZpZGVyVHlwZSI6Ikdvb2dsZSIsImlzc3VlciI6bnVsbCwicHJpbWFyeSI6InRydWUifV0sInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzU2OTMwMzYxLCJuYW1lIjoiS29uc3RhbnR5biBOb3Zvc2Vsb3YiLCJleHAiOjE3NTY5MzM5NjEsImlhdCI6MTc1NjkzMDM2MSwianRpIjoiM2Q4ZmZiZDAtZDNkYS00NzNhLTgwN2EtOGU0ZWU3YzE4YjczIiwiZW1haWwiOiJrbm92b3NlbG92QGdtYWlsLmNvbSJ9.R800lkRJ881PobnFTpkrWIN2lipF3pzZlwAp58b-ZZP2x0wRs-0uZkrl-_U4Pdj8I2ZaCUt5u2JhcDfmClaEZPn9XJoeLC5pfGrFHMcV4JfWPbOhfP-QD0snH4Rkn_KpwUzZJ41L7AjdXNWfj1gQLswo1GQ0r-plDWIJzhiMT4ju1eWn1M51OSosic7nFIrNGTp9_GmWgQkv-3rdS-e-CAAUolPTkDX1n1vtPUWyXbtCLkPewPFVRy9dnE_bIjZmsIQqNhLkMI2lZ30z7kjbqzktWfwblBmjYYRcqeIFtyKxENiQ60oKbUPpu_gv39zoaMiCcwG2o6obeqIZTW_DEg"



curl -X GET -H "Authorization: Bearer ${ACCESS_TOKEN}" ${API_URL}/user


#echo ""
#echo "logout"
# curl -I -X GET "https://auth.diviz.knovoselov.com/logout?client_id=5tb6pekknkes6eair7o39b3hh7&logout_uri=https%3A%2F%2Fdiviz.knovoselov.com"
