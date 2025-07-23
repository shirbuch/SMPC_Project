#!/usr/bin/env python3
"""
Certificate generation script for SMPC system.
Generates a CA certificate and individual certificates for each component.
"""

import os
import socket
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime
from party import Party, Share

KEY_SIZE = 3072
PUBLIC_EXPONENT = 65537

def generate_ca_certificate():
    """Generate Certificate Authority (CA) certificate"""
    print("Generating CA certificate...")
    
    ca_private_key = rsa.generate_private_key(
        public_exponent=PUBLIC_EXPONENT,
        key_size=KEY_SIZE,
    )

    ca_subject = ca_issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IL"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "IL"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Beer Sheva"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SMPC System CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SMPC Root CA"),
    ])

    ca_cert = x509.CertificateBuilder().subject_name(
        ca_subject
    ).issuer_name(
        ca_issuer
    ).public_key(
        ca_private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now()
    ).not_valid_after(
        datetime.datetime.now() + datetime.timedelta(days=3650)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    ).add_extension(
        x509.KeyUsage(
            key_cert_sign=True,
            crl_sign=True,
            digital_signature=False,
            key_encipherment=False,
            key_agreement=False,
            content_commitment=False,
            data_encipherment=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).sign(ca_private_key, hashes.SHA384())

    os.makedirs("certs", exist_ok=True)
    with open("certs/ca_key.pem", "wb") as f:
        f.write(ca_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open("certs/ca_cert.pem", "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    print("✅ CA certificate generated: certs/ca_cert.pem")
    return ca_private_key, ca_cert


def generate_component_certificate(name: str, ca_private_key, ca_cert, is_server=True):
    """Generate certificate for a system component"""
    print(f"Generating certificate for {name}...")

    private_key = rsa.generate_private_key(
        public_exponent=PUBLIC_EXPONENT,
        key_size=KEY_SIZE,
    )

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IL"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "IL"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Beer Sheva"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SMPC System"),
        x509.NameAttribute(NameOID.COMMON_NAME, name),
    ])

    cert_builder = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now()
    ).not_valid_after(
        datetime.datetime.now() + datetime.timedelta(days=365)
    )

    san_list = [
        x509.DNSName("localhost"),
        x509.DNSName(name),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]
    if is_server:
        try:
            san_list.append(x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")))
        except Exception:
            pass

    cert_builder = cert_builder.add_extension(
        x509.SubjectAlternativeName(san_list),
        critical=False,
    )

    cert_builder = cert_builder.add_extension(
        x509.KeyUsage(
            key_cert_sign=False,
            crl_sign=False,
            digital_signature=True,
            key_encipherment=True,
            key_agreement=False,
            content_commitment=False,
            data_encipherment=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )

    cert_builder = cert_builder.add_extension(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTH if is_server else ExtendedKeyUsageOID.CLIENT_AUTH
        ]),
        critical=True,
    )

    cert = cert_builder.sign(ca_private_key, hashes.SHA256())

    key_filename = f"certs/{name}_key.pem"
    with open(key_filename, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    cert_filename = f"certs/{name}_cert.pem"
    with open(cert_filename, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"✅ Certificate generated: {cert_filename}")
    return private_key, cert


def main():
    print("=" * 60)
    print("SMPC SYSTEM CERTIFICATE GENERATOR")
    print("=" * 60)

    try:
        ca_private_key, ca_cert = generate_ca_certificate()
        generate_component_certificate("Controller", ca_private_key, ca_cert, is_server=True)
        cert_names = [f"{Party(i).get_name()}" for i in range(1, 7)]
        for name in cert_names:
            generate_component_certificate(name, ca_private_key, ca_cert, is_server=True)

        print("\n" + "=" * 60)
        print("CERTIFICATE GENERATION COMPLETE")
        print("=" * 60)
        print("Generated certificates:")
        print("  📁 certs/ca_cert.pem         - Certificate Authority")
        print("  📁 certs/controller_cert.pem - Controller certificate")
        for name in cert_names:
            print(f"  📁 certs/{name}_cert.pem    - {name} certificate")
        print("\nAll communications will now be encrypted with TLS!")
        print("The CA certificate will be used to verify all connections.")

    except ImportError:
        print("❌ Error: cryptography library not installed.")
        print("Install with: pip install cryptography")
        return False
    except Exception as e:
        print(f"❌ Error generating certificates: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
