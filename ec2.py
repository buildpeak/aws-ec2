import os
import boto3

import dotenv
from optparse import OptionParser


dotenv.load_dotenv(dotenv.find_dotenv())

aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)

ec2 = boto3.client(
    "ec2",
    region_name="ap-southeast-1",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)


def list_instances(instanceId=None, keyName=None):
    res = ec2.describe_instances()

    instances = []
    for reservation in res["Reservations"]:
        for instance in reservation["Instances"]:
            if instanceId is not None and instance["InstanceId"] == instanceId:
                instances.append(instance)
            if keyName is not None and instance["KeyName"] == keyName:
                instances.append(instance)
    return instances


def list_addresses():
    res = ec2.describe_addresses()
    return res["Addresses"]


def associate_address(instanceId, allocationId):
    res = ec2.associate_address(
        InstanceId=instanceId,
        AllocationId=allocationId,
    )

    return res

def disassociate_address(associationId):
    res = ec2.disassociate_address(
        AssociationId=associationId,
    )

    return res

def release_address(allocationId):
    res = ec2.release_address(
        AllocationId=allocationId,
    )

    return res

def allocate_address():
    res = ec2.allocate_address()
    return res

def renew_address(keyName=None):
    instanceId = list_instances(keyName=keyName)[0]["InstanceId"]

    print("Renewing address for instance %s" % instanceId)

    addresses = list_addresses()

    address = None

    for addr in addresses:
        if addr["InstanceId"] == instanceId:
            address = addr
            break

    if address is not None:
        print("Disassociating address %s" % address["PublicIp"])
        disassociate_address(address["AssociationId"])
        release_address(address["AllocationId"])

    unassociated_addresses = []

    for addr in addresses:
        if "InstanceId" not in addr:
            unassociated_addresses.append(addr)

    if len(unassociated_addresses) == 0:
        print("Allocating new address")
        address = allocate_address()
    else:
        address = unassociated_addresses[0]

    print("Associating address %s" % address["PublicIp"])
    associate_address(instanceId, address["AllocationId"])



def parse_options():
    parser = OptionParser()

    return parser.parse_args()


def main():
    (_, args) = parse_options()

    if args[0] == "instances" or args[0] == "instance":
        list_instances()
    elif args[0] == 'renew-address':
        if len(args) < 2:
            print("Missing key name")
            return
        renew_address(keyName=args[1])
    else:
        print("Unknown command: %s" % args[0])


if __name__ == "__main__":
    main()
