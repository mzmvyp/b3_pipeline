import boto3

def estimate_glue_cost(data_size_mb):
    # Estimar custo do Glue baseado no tamanho dos dados
    dpu_hours = data_size_mb / 1000 * 0.1  # Estimativa
    cost_estimate = dpu_hours * 0.44
    return cost_estimate

def check_monthly_spend():
    # Verificar gastos do mês usando Cost Explorer API
    pass