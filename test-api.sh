#export API_URL="https://diviz.knovoselov.com/api"
export API_URL="http://localhost:8000/api"


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

export ACCESS_TOKEN="eyJraWQiOiJyZW5laHBEZmh0TW5FS0V5akNocTlOMmIrMHlXZEtJbUxNWFFxQnhETUdJPSIsImFsZyI6IlJTMjU2In0.eyJhdF9oYXNoIjoiM2NRQU9LNnBwRUJXM1Jka3B3b0dtQSIsInN1YiI6ImUxOWI3NTkwLWUwMDEtNzBmNy1jNTZlLWM3NjIxODYwMmE2YiIsImNvZ25pdG86Z3JvdXBzIjpbInVzLWVhc3QtMl9HU05kcktEWEVfR29vZ2xlIl0sImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMi5hbWF6b25hd3MuY29tXC91cy1lYXN0LTJfR1NOZHJLRFhFIiwiY29nbml0bzp1c2VybmFtZSI6Imdvb2dsZV8xMTEwMTc3NDYyODMxMjc1MjM4OTEiLCJub25jZSI6Ik5idkItTDA3Rzc4UG9feVMtaUVpRmpLWXZodWk5QUp3eElkcERRNHlXaDBLbllFNWVDOGluMHp1VWdCQjI4RFZNREJjbXdIRnNUanE4bjZNTFh3VlFEMmxfTVdKTnNBLXpwM0pKWVJjRXl0Y2FSSXBtR2tyUTNjdThsWkRVa29Vd1NIS2hRejB1VzMtZnpMT1U2OVlUbnZHSVJfVkJMdDRLaUdUZ3ZDRElqZyIsIm9yaWdpbl9qdGkiOiJiODgzNjAyZS1jMjc0LTQ5OGYtYTdjOS1lMGM4YjQxM2E4Y2UiLCJhdWQiOiI1dGI2cGVra25rZXM2ZWFpcjdvMzliM2hoNyIsImlkZW50aXRpZXMiOlt7ImRhdGVDcmVhdGVkIjoiMTc1Njc3MjY4NjA3MyIsInVzZXJJZCI6IjExMTAxNzc0NjI4MzEyNzUyMzg5MSIsInByb3ZpZGVyTmFtZSI6Ikdvb2dsZSIsInByb3ZpZGVyVHlwZSI6Ikdvb2dsZSIsImlzc3VlciI6bnVsbCwicHJpbWFyeSI6InRydWUifV0sInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzU3Mjk0NzAyLCJuYW1lIjoiS29uc3RhbnR5biBOb3Zvc2Vsb3YiLCJleHAiOjE3NTcyOTgzMDIsImlhdCI6MTc1NzI5NDcwMiwianRpIjoiYjRhZjYxOTQtN2Y1Yy00MjliLTllYjEtYTI4M2IxMWY1NzJmIiwiZW1haWwiOiJrbm92b3NlbG92QGdtYWlsLmNvbSJ9.CFvr8ZFq6d36OzfgYjYtHRlyC-vAqGUeo44IH_WYQjeIam6yDe8JGOqinBehWau1mNayv_TojbjTFZOyBUPB0z9S3s0lIiDCQgYaLB31hUu1wqGqRnJpcDqYnyI2T27xOUOpKeQWLnfedMCAOpD0jUqiHU8VPsgoAb5s78UAVUoUL3G7ic_TwQmz7AiG9hiCkg4xJF37VfvReZt7Smnb8IzEW2NkGuslqIqadYF1IMxnGIHpYz8Wq7ERmzq7c5xB_2kDnhHPiXmf-yLZ2eqGrK_--fUd-BdWC8BMuFA9VeGMt80K5Odp4nFX_R6yMG7rcp2CQ1zZhLO_wqpAtC5fMQ"



curl -X GET -H "Authorization: Bearer ${ACCESS_TOKEN}" ${API_URL}/user

curl -X GET -H "Authorization: Bearer ${ACCESS_TOKEN}" "${API_URL}/fireflies/hnw-kiig-zah"


TypeError: p.summary.bullet_gist.map is not a function

#echo ""
#echo "logout"
# curl -I -X GET "https://auth.diviz.knovoselov.com/logout?client_id=5tb6pekknkes6eair7o39b3hh7&logout_uri=https%3A%2F%2Fdiviz.knovoselov.com"
