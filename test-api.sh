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

export ACCESS_TOKEN="eyJraWQiOiJyZW5laHBEZmh0TW5FS0V5akNocTlOMmIrMHlXZEtJbUxNWFFxQnhETUdJPSIsImFsZyI6IlJTMjU2In0.eyJhdF9oYXNoIjoiQjNnZjgwZGp4ZWh5QmU1VXZnWXNNZyIsInN1YiI6ImUxOWI3NTkwLWUwMDEtNzBmNy1jNTZlLWM3NjIxODYwMmE2YiIsImNvZ25pdG86Z3JvdXBzIjpbInVzLWVhc3QtMl9HU05kcktEWEVfR29vZ2xlIl0sImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMi5hbWF6b25hd3MuY29tXC91cy1lYXN0LTJfR1NOZHJLRFhFIiwiY29nbml0bzp1c2VybmFtZSI6Imdvb2dsZV8xMTEwMTc3NDYyODMxMjc1MjM4OTEiLCJub25jZSI6IlIzM1BlNkRLU21tOHhrYnJNcno5ZGJCRzVTSDNQQkJPWE1nRUhORlUzdGstTmhNR1RiRWRYR25iLXMzeGZIeWhVbHFnUFlTTE5KY2NQWWcyMU8yZ3hVeXJKRERvZTFWNW9BYzY2Z0x4ekN6UnpqSDdkeHpSa1Ztb3ZoN1FLMnJBSG9qWXo1dFp5QTN3UUdncEVPQkhsam5qYXFMREt0TUV5aGtFUmtpWGVWZyIsIm9yaWdpbl9qdGkiOiJjM2Y4ZGMwOC05ZWEzLTRiM2UtYWYzNS03ODVhMWFiYWEzMjQiLCJhdWQiOiI1dGI2cGVra25rZXM2ZWFpcjdvMzliM2hoNyIsImlkZW50aXRpZXMiOlt7ImRhdGVDcmVhdGVkIjoiMTc1Njc3MjY4NjA3MyIsInVzZXJJZCI6IjExMTAxNzc0NjI4MzEyNzUyMzg5MSIsInByb3ZpZGVyTmFtZSI6Ikdvb2dsZSIsInByb3ZpZGVyVHlwZSI6Ikdvb2dsZSIsImlzc3VlciI6bnVsbCwicHJpbWFyeSI6InRydWUifV0sInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzU3Mjg4NzY3LCJuYW1lIjoiS29uc3RhbnR5biBOb3Zvc2Vsb3YiLCJleHAiOjE3NTcyOTIzNjcsImlhdCI6MTc1NzI4ODc2NywianRpIjoiZGUyOWIwNWEtZGMzNi00NDk3LThhN2QtN2ZlNWM3OTE5NDMyIiwiZW1haWwiOiJrbm92b3NlbG92QGdtYWlsLmNvbSJ9.OMd-tBMPE03vkA2lF0CwFZtMpI_8UvFtZjjBi4ir8gIeazuntS_kgOR8lQaeZ1ZnFUjiKeSJkd08Gv7b0fcqdVBt1gsokqYNwLHyoDp1fckx-MzmC0zRP6ojwOMpd-YF2WgrH1q83JdUKWnmR13VoE3hoReQYYD4TrkYWajzAlUFesZLBAccd_stAeMn3Rga3gZgnlC98OyxhbZSxo-EJ2FCoh4CqJxIBM9DF5CMDNd0SpCO_vc3C2YvVMiXo6kZ7BjD_9bc03GQ-Ejq9M2fPoHlRKlB1CXljH_BSWiramcYelcSu2KkTebBn6F_QxZHmXUvXVCdGw8fWzRw5-YKqQ"



curl -X GET -H "Authorization: Bearer ${ACCESS_TOKEN}" ${API_URL}/user

curl -X GET -H "Authorization: Bearer ${ACCESS_TOKEN}" "${API_URL}/fireflies/hnw-kiig-zah?days=20"


#echo ""
#echo "logout"
# curl -I -X GET "https://auth.diviz.knovoselov.com/logout?client_id=5tb6pekknkes6eair7o39b3hh7&logout_uri=https%3A%2F%2Fdiviz.knovoselov.com"
