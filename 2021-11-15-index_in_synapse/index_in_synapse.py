# Import packages
import synapseclient
import json

# Create custom storage location (owner.txt must exist at this stage)
syn = synapseclient.login()
destination = {
    "uploadType": "S3",
    "concreteType": "org.sagebionetworks.repo.model.project.ExternalS3StorageLocationSetting",
    "bucket": "example-dev-project-tower-bucket",
}
destination = syn.restPOST("/storageLocation", body=json.dumps(destination))

# Create a file handle for an S3 object
fileHandle = {
    "concreteType": "org.sagebionetworks.repo.model.file.S3FileHandle",
    "storageLocationId": destination["storageLocationId"],
    "fileName": "tcrb-samples-sarek.tsv",
    "contentMd5": "a25ba594d3c39a5eab8d02d6deee6e87",
    # "contentSize": "382",                         # Optional
    # "contentType": "text/tab-separated-values",   # Optional
}
fileHandle = syn.restPOST(
    "/externalFileHandle/s3", json.dumps(fileHandle), endpoint=syn.fileHandleEndpoint
)

# Expose that file handle on Synapse with a File
f = synapseclient.File(
    name=fileHandle["fileName"],
    parentId="syn23529995",
    dataFileHandleId=fileHandle["id"],
)
f = syn.store(f)
