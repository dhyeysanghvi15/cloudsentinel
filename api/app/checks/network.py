from __future__ import annotations

import boto3

from ..models import CheckResult


SENSITIVE_PORTS = {22, 3389, 5432, 3306, 6379, 9200, 27017}


def check_sg_open_sensitive_ports(session: boto3.session.Session, region: str) -> CheckResult:
    ec2 = session.client("ec2", region_name=region)
    open_rules: list[dict] = []
    try:
        resp = ec2.describe_security_groups(MaxResults=200)
        for sg in resp.get("SecurityGroups", []):
            for perm in sg.get("IpPermissions", []):
                from_port = perm.get("FromPort")
                to_port = perm.get("ToPort")
                if from_port is None or to_port is None:
                    continue
                ports = set(range(int(from_port), int(to_port) + 1))
                if not (ports & SENSITIVE_PORTS):
                    continue
                for ip in perm.get("IpRanges", []):
                    if ip.get("CidrIp") == "0.0.0.0/0":
                        open_rules.append(
                            {
                                "group_id": sg.get("GroupId"),
                                "group_name": sg.get("GroupName"),
                                "from": from_port,
                                "to": to_port,
                                "cidr": "0.0.0.0/0",
                            }
                        )

        status = "pass" if not open_rules else "fail"
        return CheckResult(
            id="net.sg_open_sensitive_ports",
            title="Security groups open to 0.0.0.0/0 on sensitive ports",
            severity="critical",
            status=status,
            domain="Network Exposure",
            evidence={"findings": open_rules[:25], "count": len(open_rules), "ports": sorted(SENSITIVE_PORTS)},
            recommendation="Restrict inbound rules: remove 0.0.0.0/0 access on admin/database ports; use VPN/bastion/SSM.",
            references=["https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html"],
            weight=15,
        )
    except Exception as e:
        return CheckResult(
            id="net.sg_open_sensitive_ports",
            title="Security groups open to 0.0.0.0/0 on sensitive ports",
            severity="critical",
            status="error",
            domain="Network Exposure",
            evidence={"error": str(e)},
            recommendation="Ensure the scanning role can call ec2:DescribeSecurityGroups.",
            references=[],
            weight=15,
        )

