#!/usr/bin/env python3

# The following script was adapted from:
# https://gist.github.com/amalgjose/9007f5aac9e9751d595a5232fa3dd6bf

import sys

import boto3
import requests
import synapseclient, synapseutils

SYN_ENTITY = sys.argv[1]
S3_BUCKET = sys.argv[2]
S3_ROOT_KEY = sys.argv[3]

syn = synapseclient.login(silent=True)
session = requests.Session()
s3 = boto3.client("s3")

# Iterate over all files within the Synapse container
for dirpath, dirnames, filenames in synapseutils.walk(syn, SYN_ENTITY):
    dirname, dirid = dirpath
    for filename, fileid in filenames:
        # Build S3 object key and URI
        subdirname = dirname.partition("/")[2]
        if subdirname:
            filename = f"{subdirname}/{filename}"
        s3_key = f"{S3_ROOT_KEY}/{filename}"
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
        # Retrieve the pre-signed URL from Synapse
        file = syn.get(fileid, downloadFile=False)
        if not file.concreteType.endswith("FileEntity"):
            continue
        handle_id = file._file_handle.id
        url_params = {
            "redirect": False,
            "fileAssociateType": "FileEntity",
            "fileAssociateId": fileid,
        }
        presigned_url = syn.restGET(
            f"/file/{handle_id}",
            syn.fileHandleEndpoint,
            requests_session=session,
            params=url_params,
        )
        # Stream URL response to S3 using multipart upload
        print(f"{fileid} --> {s3_uri}")
        response = session.get(presigned_url, stream=True)
        with response as part:
            part.raw.decode_content = True
            conf = boto3.s3.transfer.TransferConfig(
                multipart_threshold=10000, max_concurrency=4
            )
            s3.upload_fileobj(part.raw, S3_BUCKET, s3_key, Config=conf)
