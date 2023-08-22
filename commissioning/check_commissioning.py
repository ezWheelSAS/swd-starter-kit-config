#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from typing import List

from colorama import Fore, Style

sys.path.append("/opt/ezw/usr/lib")  # smcdbusclient/

from smcdbusclient.communication import BitTiming, PDOTransmissionType, PDOId, CommunicationDBusClient
from smcdbusclient.pds import PDSDBusClient
from smcdbusclient.safe_motion import STOId, SLSId, SafetyFunctionId, SafetyWordMapping, SafeMotionDBusClient, SafetyControlWordId

from smcdbusclient.nmt import NMTDBusClient

from smcdbusclient.velocity_mode import VelocityModeDBusClient

from smcdbusclient.manufacturer import ManufacturerDBusClient

from smcdbusclient.can_open import CANOpenDBusClient
from smcdbusclient.srdo import SRDODBusClient, SRDOId

nmt_client = None
pds_client = None
safe_motion_client = None
velocity_mode_client = None
communication_client = None
manufacturer_client = None
srdo_client = None


def check(msg: str, error: int):
    if error == 1:  # ERROR_NONE
        print(f"{msg} : {Fore.GREEN}OK{Style.RESET_ALL}")
    else:
        print(f"{msg} : {Fore.RED}Failed{Style.RESET_ALL}")

        # Exit
        print("\nCheck commissioning failed !")
        sys.exit(1)


def swm_bit(swm: SafetyWordMapping, bit: int) -> SafetyFunctionId:
    return getattr(swm, "safety_function_" + str(bit))


def eq_swm(a: List[SafetyFunctionId], b: SafetyWordMapping):
    for i in range(0, len(a)):
        if a[i] != swm_bit(b, i):
            return 0
    return 1


def check_network_parameters(node_id: int):
    params, error = communication_client.getNetworkParameters()

    if error != 1 or params.node_id != node_id or params.bit_timing != BitTiming.BT_1000 or params.rt_activated != True:
        error = 0

    check(f"check NetworkParameters(node_id={node_id})", error)


def check_polarity_parameters(polarity: bool):
    params, error = pds_client.getPolarityParameters()

    if error != 1 or params.velocity_polarity != polarity or params.position_polarity != polarity:
        error = 0

    check(f"check PolarityParameters({polarity})", error)


def check_ramps(vl_acc_delta_speed: int, vl_dec_delta_speed: int):
    params, error = velocity_mode_client.getVelocityModeParameters()
    if error != 1 or params.vl_velocity_acceleration_delta_speed != vl_acc_delta_speed or params.vl_velocity_deceleration_delta_speed != vl_dec_delta_speed:
        error = 0

    check(f"check VelocityModeParameters({vl_acc_delta_speed},{vl_dec_delta_speed})", error)


def check_STO_parameters(restart_acknowledge_behavior: bool):
    params, _, error = safe_motion_client.getSTOParameters(STOId.STO_1)
    if error != 1 or params.restart_acknowledge_behavior != restart_acknowledge_behavior:
        error = 0

    check(f"check STOParameters({restart_acknowledge_behavior})", error)


def check_SLS_parameters(sls_vl_limit: int, sls_vl_time_monitoring: int):
    params, _, error = safe_motion_client.getSLSParameters(SLSId.SLS_1)
    if (
        error != 1
        or params.velocity_limit_u32 != sls_vl_limit
        or params.time_to_velocity_monitoring != sls_vl_time_monitoring
        or params.time_for_velocity_in_limits != sls_vl_time_monitoring
    ):
        error = 0

    check(f"check SLSParameters({sls_vl_limit},{sls_vl_time_monitoring})", error)


def check_error_behavior(error_behavior: int):
    value, error = can_open_client.getValueUInt8(0x1029_02_00)

    if error != 1 or value != error_behavior:
        error = 0

    check(f"check ErrorBehavior({error_behavior})", error)


def check_SWD_parameters(pid_p: int, pid_i: int, pid_d: int):
    params, error = manufacturer_client.getSWDParameters()
    if error != 1 or params.motctrl_speed_pid_p != pid_p or params.motctrl_speed_pid_i != pid_i or params.motctrl_speed_pid_d != pid_d:
        error = 0

    check(f"check SWDParameters({pid_p},{pid_i},{pid_d})", error)


def check_SRDO_parameters_left():
    for srdo in SRDOId:
        if srdo != SRDOId.SRDO_9 and srdo != SRDOId.SRDO_16:
            _, params, _, error = srdo_client.getSRDOParameters(srdo)
            if error != 1 or params.valid != False:
                error = 0
                break

    if error == 1:
        _, params, _, error = srdo_client.getSRDOParameters(SRDOId.SRDO_9)
        if error != 1 or params.can_id1 != 0x109 or params.can_id2 != 0x10A or params.valid != True or params.sct != 50 or params.srvt != 20:
            error = 0

    if error == 1:
        scw_mapping = [
            SafetyFunctionId.STO,
            SafetyFunctionId.STO,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
        ]
        value, error = safe_motion_client.getSafetyControlWordMapping(SafetyControlWordId.CAN_2)
        if error != 1 or eq_swm(scw_mapping, value) != 1:
            error = 0

    if error == 1:
        _, params, _, error = srdo_client.getSRDOParameters(SRDOId.SRDO_16)
        if error != 1 or params.can_id1 != 0x160 or params.can_id2 != 0x161 or params.valid != True or params.sct != 25 or params.srvt != 20:
            error = 0

    if error == 1:
        scw_mapping = [
            SafetyFunctionId.STO,
            SafetyFunctionId.STO,
            SafetyFunctionId.SDIN_1,
            SafetyFunctionId.SDIN_1,
            SafetyFunctionId.SLS_1,
            SafetyFunctionId.SLS_1,
        ]
        value, error = safe_motion_client.getSafetyControlWordMapping(SafetyControlWordId.SAFEIN_1)
        if error != 1 or eq_swm(scw_mapping, value) != 1:
            error = 0

    if error == 1:
        value, error = srdo_client.getSRDOConfigurationValidity()
        if error != 1 and value != False:
            error = 0

    check(f"check SRDOParameters(node_id=4)", error)


def check_SRDO_parameters_right():
    for srdo in SRDOId:
        if srdo != SRDOId.SRDO_9 and srdo != SRDOId.SRDO_16:
            _, params, _, error = srdo_client.getSRDOParameters(srdo)
            if error != 1 or params.valid != False:
                error = 0
                break

    if error == 1:
        _, params, _, error = srdo_client.getSRDOParameters(SRDOId.SRDO_9)
        if error != 1 or params.can_id1 != 0x160 or params.can_id2 != 0x161 or params.valid != True or params.sct != 50 or params.srvt != 20:
            error = 0

    if error == 1:
        scw_mapping = [
            SafetyFunctionId.STO,
            SafetyFunctionId.STO,
            SafetyFunctionId.SDIP_1,
            SafetyFunctionId.SDIP_1,
            SafetyFunctionId.SLS_1,
            SafetyFunctionId.SLS_1,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
        ]
        value, error = safe_motion_client.getSafetyControlWordMapping(SafetyControlWordId.CAN_2)
        if error != 1 or eq_swm(scw_mapping, value) != 1:
            error = 0

    if error == 1:
        _, params, _, error = srdo_client.getSRDOParameters(SRDOId.SRDO_16)
        if error != 1 or params.can_id1 != 0x109 or params.can_id2 != 0x10A or params.valid != True or params.sct != 25 or params.srvt != 20:
            error = 0

    if error == 1:
        scw_mapping = [
            SafetyFunctionId.STO,
            SafetyFunctionId.STO,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
            SafetyFunctionId.NONE,
        ]
        value, error = safe_motion_client.getSafetyControlWordMapping(SafetyControlWordId.SAFEIN_1)
        if error != 1 or eq_swm(scw_mapping, value) != 1:
            error = 0

    if error == 1:
        value, error = srdo_client.getSRDOConfigurationValidity()
        if error != 1 and value != False:
            error = 0

    check(f"check SRDOParameters(node_id=5)", error)


def check_communication_parameters(node_id):

    # TPDO_1
    valid = True
    params, error = communication_client.getTPDOCommunicationParameters(PDOId.PDO_1)
    if (
        error != 1
        or params.cob_id.can_id != 0x180 + node_id
        or params.cob_id.valid != valid
        or params.cob_id.flag != True
        or params.transmission_type != PDOTransmissionType.PDO_SYNC_1
    ):
        error = 0

    # TPDO_2
    valid = True
    if error == 1:
        params, error = communication_client.getTPDOCommunicationParameters(PDOId.PDO_2)
        if (
            error != 1
            or params.cob_id.can_id != 0x280 + node_id
            or params.cob_id.valid != valid
            or params.cob_id.flag != True
            or params.transmission_type != PDOTransmissionType.PDO_SYNC_1
        ):
            error = 0

    # TPDO_3
    valid = True
    if error == 1:
        params, error = communication_client.getTPDOCommunicationParameters(PDOId.PDO_3)
        if (
            error != 1
            or params.cob_id.can_id != 0x380 + node_id
            or params.cob_id.valid != valid
            or params.cob_id.flag != True
            or params.transmission_type != PDOTransmissionType.PDO_SYNC_1
        ):
            error = 0

    # TPDO_4
    valid = True
    if error == 1:
        params, error = communication_client.getTPDOCommunicationParameters(PDOId.PDO_4)
        if (
            error != 1
            or params.cob_id.can_id != 0x480 + node_id
            or params.cob_id.valid != valid
            or params.cob_id.flag != True
            or params.transmission_type != PDOTransmissionType.PDO_SYNC_1
        ):
            error = 0

    # RPDO_1
    valid = True
    if error == 1:
        params, error = communication_client.getRPDOCommunicationParameters(PDOId.PDO_1)
        if (
            error != 1
            or params.cob_id.can_id != 0x200 + node_id
            or params.cob_id.valid != valid
            or params.cob_id.flag != True
            or params.transmission_type != PDOTransmissionType.PDO_SYNC_1
        ):
            error = 0

    # RPDO_2
    valid = False
    if error == 1:
        params, error = communication_client.getRPDOCommunicationParameters(PDOId.PDO_2)
        if (
            error != 1
            or params.cob_id.can_id != 0x300 + node_id
            or params.cob_id.valid != valid
            or params.cob_id.flag != True
            or params.transmission_type != PDOTransmissionType.PDO_SYNC_1
        ):
            error = 0

    # RPDO_3
    valid = False
    if error == 1:
        params, error = communication_client.getRPDOCommunicationParameters(PDOId.PDO_3)
        if (
            error != 1
            or params.cob_id.can_id != 0x400 + node_id
            or params.cob_id.valid != valid
            or params.cob_id.flag != True
            or params.transmission_type != PDOTransmissionType.PDO_SYNC_1
        ):
            error = 0

    # RPDO_4
    valid = True
    if error == 1:
        params, error = communication_client.getRPDOCommunicationParameters(PDOId.PDO_4)
        if (
            error != 1
            or params.cob_id.can_id != 0x500 + node_id
            or params.cob_id.valid != valid
            or params.cob_id.flag != True
            or params.transmission_type != PDOTransmissionType.PDO_SYNC_1
        ):
            error = 0

    # TPDO1 communication mapping
    if error == 1:
        params, error = communication_client.getTPDOMappingParameters(PDOId.PDO_1)
        if error != 1 or params.nb != 1 or 0x2620_02_08 not in params.items:
            error = 0

    # TPDO3 communication mapping
    if error == 1:
        params, error = communication_client.getTPDOMappingParameters(PDOId.PDO_3)
        if error != 1 or params.nb != 2 or 0x6041_00_10 not in params.items or 0x6064_00_20 not in params.items:
            error = 0

    check(f"check TPDOCommunicationParameters(node_id={node_id})", error)


# Init
def create_dbus_clients(instance_id: str):
    import os

    global nmt_client
    global pds_client
    global safe_motion_client
    global velocity_mode_client
    global communication_client
    global can_open_client
    global manufacturer_client
    global srdo_client

    # Load specific dbus user session if exists
    if os.path.isfile("/tmp/SYSTEMCTL_dbus.id"):
        #        print("SYSTEMCTL_dbus.id detected")
        with open("/tmp/SYSTEMCTL_dbus.id") as f:
            lines = f.readlines()
        env = dict(line.strip().split("=", 1) for line in lines)
        os.environ.update(env)

    nmt_client = NMTDBusClient(instance_id)
    pds_client = PDSDBusClient(instance_id)
    safe_motion_client = SafeMotionDBusClient(instance_id)
    velocity_mode_client = VelocityModeDBusClient(instance_id)
    communication_client = CommunicationDBusClient(instance_id)
    can_open_client = CANOpenDBusClient(instance_id)
    manufacturer_client = ManufacturerDBusClient(instance_id)
    srdo_client = SRDODBusClient(instance_id)


# =======================
#      MAIN PROGRAM
# =======================


def main(argv):
    swd_id = argv[0]
    instance_id = f"swd_{swd_id}"
    node_id = 0x4 if swd_id == "left" else 0x5
    polarity = True if swd_id == "left" else False
    vl_acc_delta_speed = 1500
    vl_dec_delta_speed = 1500
    restart_acknowledge_behavior = False
    sls_vl_limit = 680
    sls_vl_time_monitoring = 1000
    error_behavior = 1
    pid_p = 200
    pid_i = 10
    pid_d = 0  # Do not change

    # Create DBus clients
    create_dbus_clients(instance_id)

    #
    # Check Network parameters
    #
    check_network_parameters(node_id)

    #
    # Check PDO communication parameters
    #
    check_communication_parameters(node_id)

    #
    # Check Polarity parameters
    #
    check_polarity_parameters(polarity)

    #
    # Check SRDO parameters
    #
    if swd_id == "left":
        check_SRDO_parameters_left()
    else:
        check_SRDO_parameters_right()
    #
    # Check Ramps
    #
    check_ramps(vl_acc_delta_speed, vl_dec_delta_speed)

    #
    # Check STO parameters
    #
    check_STO_parameters(restart_acknowledge_behavior)

    #
    # Check SLS parameters
    #
    check_SLS_parameters(sls_vl_limit, sls_vl_time_monitoring)

    #
    # Check error behavior
    #
    check_error_behavior(error_behavior)

    #
    # Check SWD parameters
    #
    check_SWD_parameters(pid_p, pid_i, pid_d)

    # Exit with success
    print("\nCheck commissioning succeeded !")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Missing swd motor argument : [left|right]")
        exit(1)

    if len(sys.argv) > 2:
        print("Too many arguments")
        exit(1)

    if sys.argv[1] != "left" and sys.argv[1] != "right":
        print("Invalid motor argument : [left|right]")
        exit(1)

    main(sys.argv[1:])
