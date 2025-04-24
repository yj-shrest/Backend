from walrus import WalrusClient

publisher_url = "https://publisher.testnet.walrus.atalma.io"
aggregator_url = "https://agg.test.walrus.eosusa.io"


client = WalrusClient(publisher_base_url=publisher_url, aggregator_base_url=aggregator_url)


def store_blob(blob_data):
    response = client.put_blob(data=blob_data,epochs=10)
    print(response)
    blobid = ''
    if 'newlyCreated' in response and 'blobObject' in response['newlyCreated']:
        blobid = response['newlyCreated']['blobObject']['blobId']
    else:
        blobid = response['alreadyCertified']['blobId']
    return blobid


def get_blob(blob_id):
    print(f"Getting blob with ID: {blob_id}")
    response = client.get_blob(blob_id)
    print(response)
    return response

def store_image(image_path):
    response = client.put_blob_from_file(image_path, epochs=10)
    print(response)
    blobid = ''
    if 'newlyCreated' in response and 'blobObject' in response['newlyCreated']:
        blobid = response['newlyCreated']['blobObject']['blobId']
    else:
        blobid = response['alreadyCertified']['blobId']
    return blobid

def get_and_save_image(blob_id, save_path):
    response = client.get_blob(blob_id)
    with open(save_path, 'wb') as f:
        f.write(response)
    return response

if __name__ == "__main__":
    blob = get_blob("5Uj7G06-CvU5dWNDhtmvsIVJu7CuMQL1PMggP2DZnbo")
    print(blob)