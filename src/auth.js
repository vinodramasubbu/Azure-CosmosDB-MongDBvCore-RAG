import { ClientSecretCredential } from "@azure/identity";

const getToken = async () => {
  const credential = new ClientSecretCredential(
    "b5109d14-d728-4692-833d-b4f8d9563f36",
    "e0ee106c-6c9b-4b9d-b4b3-f44827fe1799",
    "W9w8Q~~wns8JHN3Kjv7WR..7CvveyT3nb6WnmdAs"
  );
  const token = await credential.getToken("api://3877f06b-d396-4705-94dd-9115704594e1/.default");
  return token.token;
};

export default { getToken };