import axios from "axios";
const client = axios.create({
    baseURL: "/api",
    timeout: 30000
});
export async function postChat(request) {
    const { data } = await client.post("/chat", request);
    return data;
}
