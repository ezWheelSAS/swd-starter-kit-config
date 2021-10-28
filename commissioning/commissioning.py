#
# Copyright (C) 2021 ez-Wheel. All Rights Reserved.
#

import sys
from typing import List

sys.path.append("/opt/ezw/usr/lib")

from colorama import Fore, Style

from smcdbusclient.communication import NetworkParameters, BitTiming, PDOCommunicationParameters, PDOTransmissionType, PDOId, CommunicationDBusClient
from smcdbusclient.pds import PolarityParameters, PDSDBusClient
from smcdbusclient.safe_motion import STOId, SLSId, SafetyFunctionId, SafetyWordMapping, SafeMotionDBusClient

from smcdbusclient.nmt import NMTDBusClient

from smcdbusclient.velocity_mode import VelocityModeDBusClient

from smcdbusclient.srdo import SRDODBusClient, SRDOId

# global
nmt_client = None
pds_client = None
safe_motion_client = None
velocity_mode_client = None
srdo_client = None
communication_client = None

# Helpers


def check(msg: str, error: int):
    if error == 1:  # ERROR_NONE
        print(f"{msg} : {Fore.GREEN}OK{Style.RESET_ALL}")
    else:
        print(f"{msg} : {Fore.RED}Failed{Style.RESET_ALL}")

        # Exit
        print("\nCommissioning failed !")
        sys.exit(1)


def list_to_swm(l: List[SafetyFunctionId]):
    ret = SafetyWordMapping()
    for i in range(0, len(l)):
        setattr(ret, "safety_function_" + str(i), l[i])
    return ret


# Updaters


def update_network_parameters(node_id: int):

    network = NetworkParameters()

    network.node_id = node_id
    network.bit_timing = BitTiming.BT_1000
    network.rt_activated = True

    error = communication_client.setNetworkParameters(network)
    check(f"setNetworkParameters(node_id={node_id})", error)


def update_communication_parameters(node_id: int):

    params = PDOCommunicationParameters()

    params.cob_id.can_id = 0x180 + node_id  # 0x180 + $NODE_ID
    params.cob_id.valid = True
    params.cob_id.flag = True
    params.transmission_type = PDOTransmissionType.PDO_SYNC_1

    # Set the COB ID of the TPDO_1
    params.cob_id.can_id = 0x180 + node_id  # 0x180 + $NODE_ID
    error = communication_client.setTPDOCommunicationParameters(PDOId.PDO_1, params)
    check("setTPDOCommunicationParameters(PDOId.PDO_1)", error)

    # Set the COB ID of the TPDO_2
    params.cob_id.can_id = 0x280 + node_id  # 0x280 + $NODE_ID
    error = communication_client.setTPDOCommunicationParameters(PDOId.PDO_2, params)
    check("setTPDOCommunicationParameters(PDOId.PDO_2)", error)

    # Set the COB ID of the TPDO_3
    params.cob_id.can_id = 0x380 + node_id  # 0x380 + $NODE_ID
    error = communication_client.setTPDOCommunicationParameters(PDOId.PDO_3, params)
    check("setTPDOCommunicationParameters(PDOId.PDO_3)", error)

    # Set the COB ID of the TPDO_4
    params.cob_id.can_id = 0x480 + node_id  # 0x480 + $NODE_ID
    error = communication_client.setTPDOCommunicationParameters(PDOId.PDO_4, params)
    check("setTPDOCommunicationParameters(PDOId.PDO_4)", error)

    # Set the COB ID of the RPDO_1
    params.cob_id.can_id = 0x200 + node_id  # 0x200 + $NODE_ID
    error = communication_client.setRPDOCommunicationParameters(PDOId.PDO_1, params)
    check("setRPDOCommunicationParameters(PDOId.PDO_1)", error)

    # Set the COB ID of the RPDO_2
    params.cob_id.can_id = 0x300 + node_id  # 0x300 + $NODE_ID
    error = communication_client.setRPDOCommunicationParameters(PDOId.PDO_2, params)
    check("setRPDOCommunicationParameters(PDOId.PDO_2)", error)

    # Set the COB ID of the RPDO_3
    params.cob_id.can_id = 0x400 + node_id  # 0x400 + $NODE_ID
    error = communication_client.setRPDOCommunicationParameters(PDOId.PDO_3, params)
    check("setRPDOCommunicationParameters(PDOId.PDO_3)", error)

    # Set the COB ID of the RPDO_4
    params.cob_id.can_id = 0x500 + node_id  # 0x500 + $NODE_ID
    error = communication_client.setRPDOCommunicationParameters(PDOId.PDO_4, params)
    check("setRPDOCommunicationParameters(PDOId.PDO_4)", error)


def update_polarity_parameters(polarity: bool):

    params = PolarityParameters()
    params.velocity_polarity = polarity
    params.position_polarity = polarity

    error = pds_client.setPolarityParameters(params)
    check(f"setPolarityParameters({polarity})", error)


def disable_SRDO_parameters():

    # Modify every SRDO
    for srdo in SRDOId:
        (
            _,
            params,
            _,
            error,
        ) = srdo_client.getSRDOParameters(srdo)
        check(f"getSRDOParameters({srdo.name})", error)

        params.valid = False

        error = srdo_client.setSRDOParameters(srdo, params)
        check(f"setSRDOParameters({srdo.name})", error)

    error = srdo_client.setSRDOConfigurationValid()
    check("setSRDOConfigurationValid()", error)


def update_ramps(vl_dec_delta_spped):
    params, error = velocity_mode_client.getVelocityModeParameters()
    check("getVelocityModeParameters()", error)

    params.vl_velocity_deceleration_delta_speed = vl_dec_delta_spped

    error = velocity_mode_client.setVelocityModeParameters(params)
    check("setVelocityParameters()", error)


def update_STO_parameters(status):
    params, signature, error = safe_motion_client.getSTOParameters(STOId.STO_1)
    check("getSTOParameters(STOId.STO_1)", error)

    params.restart_acknowledge_behavior = status

    error = safe_motion_client.setSTOParameters(STOId.STO_1, params)
    check("setSTOParameters(STOId.STO_1)", error)

def update_SLS_parameters(vl_limit, vl_time_monitoring):
    params, signature, error = safe_motion_client.getSLSParameters(SLSId.SLS_1)
    check("getLSParameters(SLSId.SLS_1)", error)

    params.velocity_limit_u32 = vl_limit
    params.time_to_velocity_monitoring = vl_time_monitoring

    error = safe_motion_client.setSLSParameters(SLSId.SLS_1, params)
    check("setSLSParameters(SLSId.SLS_1)", error)

# Init
def create_dbus_clients(instance_id: str):
    import os
    from pathlib import Path

    global nmt_client
    global pds_client
    global safe_motion_client
    global velocity_mode_client
    global srdo_client
    global communication_client

    # Load specific dbus user session if exists
    if os.path.isfile("/opt/ezw/data/tmp/SYSTEMCTL_dbus.id"):
        print("SYSTEMCTL_dbus.id detected")
        with open("/opt/ezw/data/tmp/SYSTEMCTL_dbus.id") as f:
            lines = f.readlines()
        env = dict(line.strip().split("=", 1) for line in lines)
        os.environ.update(env)

    nmt_client = NMTDBusClient(instance_id)
    pds_client = PDSDBusClient(instance_id)
    safe_motion_client = SafeMotionDBusClient(instance_id)
    velocity_mode_client = VelocityModeDBusClient(instance_id)
    srdo_client = SRDODBusClient(instance_id)
    communication_client = CommunicationDBusClient(instance_id)

    check(f"create_dbus_clients({instance_id})", 1)
