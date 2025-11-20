# Generated manually to prepare data for CPF as primary key

import re
from django.db import migrations


def normalizar_cpfs_e_remover_duplicatas(apps, schema_editor):
    """
    Normaliza CPFs existentes e remove duplicatas de email/telefone.
    """
    Cliente = apps.get_model('cobranca_app', 'Cliente')
    
    # Normaliza todos os CPFs (remove caracteres não numéricos)
    for cliente in Cliente.objects.all():
        cpf_antigo = cliente.cpf
        cpf_novo = re.sub(r'[^0-9]', '', str(cpf_antigo))
        
        # Se o CPF normalizado for diferente, atualiza
        if cpf_antigo != cpf_novo:
            # Verifica se já existe outro cliente com este CPF normalizado
            if Cliente.objects.filter(cpf=cpf_novo).exclude(id=cliente.id).exists():
                # Se já existe, marca este para exclusão (duplicata)
                print(f"AVISO: Cliente ID {cliente.id} tem CPF duplicado. Será removido.")
                cliente.delete()
            else:
                cliente.cpf = cpf_novo
                cliente.save()
    
    # Remove duplicatas de email (mantém o primeiro)
    emails_vistos = {}
    for cliente in Cliente.objects.all().order_by('id'):
        email_lower = cliente.email.lower() if cliente.email else None
        if email_lower and email_lower in emails_vistos:
            print(f"AVISO: Cliente ID {cliente.id} tem email duplicado ({cliente.email}). Será removido.")
            cliente.delete()
        elif email_lower:
            emails_vistos[email_lower] = cliente.id
    
    # Remove duplicatas de telefone (mantém o primeiro)
    telefones_vistos = {}
    for cliente in Cliente.objects.all().order_by('id'):
        telefone_normalizado = re.sub(r'[^0-9]', '', str(cliente.telefone_whatsapp or ''))
        if telefone_normalizado and telefone_normalizado in telefones_vistos:
            print(f"AVISO: Cliente ID {cliente.id} tem telefone duplicado ({cliente.telefone_whatsapp}). Será removido.")
            cliente.delete()
        elif telefone_normalizado:
            telefones_vistos[telefone_normalizado] = cliente.id


def reverter_normalizacao(apps, schema_editor):
    """
    Função de reversão (não faz nada, pois não podemos recuperar dados deletados).
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cobranca_app', '0002_cliente_cobranca_notificacao'),
    ]

    operations = [
        migrations.RunPython(normalizar_cpfs_e_remover_duplicatas, reverter_normalizacao),
    ]


