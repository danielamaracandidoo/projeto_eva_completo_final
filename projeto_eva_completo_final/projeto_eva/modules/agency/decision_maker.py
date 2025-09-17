"""
Sistema de tomada de decisões da EVA.
Responsável por tomar decisões estruturadas e racionais.
"""

import asyncio
import json
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from utils.logging_system import EVALogger

class DecisionType(Enum):
    """Tipos de decisão"""
    BINARY = "binary"  # Sim/Não
    MULTIPLE_CHOICE = "multiple_choice"  # Múltiplas opções
    RANKING = "ranking"  # Ordenação de opções
    RESOURCE_ALLOCATION = "resource_allocation"  # Alocação de recursos
    STRATEGIC = "strategic"  # Decisões estratégicas
    OPERATIONAL = "operational"  # Decisões operacionais

class DecisionMethod(Enum):
    """Métodos de tomada de decisão"""
    WEIGHTED_SCORING = "weighted_scoring"
    PROS_CONS = "pros_cons"
    DECISION_TREE = "decision_tree"
    COST_BENEFIT = "cost_benefit"
    RISK_ANALYSIS = "risk_analysis"
    MULTI_CRITERIA = "multi_criteria"
    INTUITIVE = "intuitive"

@dataclass
class DecisionCriterion:
    """Critério de decisão"""
    name: str
    description: str
    weight: float  # 0.0 a 1.0
    is_benefit: bool = True  # True se maior valor é melhor
    measurement_scale: str = "numeric"  # numeric, categorical, boolean

@dataclass
class DecisionOption:
    """Opção de decisão"""
    id: str
    name: str
    description: str
    scores: Dict[str, float]  # criterion_name -> score
    pros: List[str] = None
    cons: List[str] = None
    estimated_cost: float = 0.0
    estimated_benefit: float = 0.0
    risk_level: float = 0.0  # 0.0 a 1.0
    implementation_difficulty: float = 0.0  # 0.0 a 1.0

@dataclass
class DecisionResult:
    """Resultado de uma decisão"""
    decision_id: str
    recommended_option: str
    confidence_level: float
    reasoning: str
    alternative_options: List[Tuple[str, float]]  # (option_id, score)
    method_used: DecisionMethod
    criteria_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    created_at: datetime

class DecisionMaker:
    """
    Sistema de tomada de decisões da EVA.
    
    Funcionalidades:
    - Múltiplos métodos de decisão
    - Análise multi-critério
    - Avaliação de riscos
    - Análise de prós e contras
    - Árvores de decisão
    - Análise custo-benefício
    - Raciocínio explicável
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("DecisionMaker")
        
        # Armazenamento de decisões
        self.decisions: Dict[str, DecisionResult] = {}
        
        # Métodos de decisão
        self.decision_methods = {
            DecisionMethod.WEIGHTED_SCORING: self._weighted_scoring_method,
            DecisionMethod.PROS_CONS: self._pros_cons_method,
            DecisionMethod.DECISION_TREE: self._decision_tree_method,
            DecisionMethod.COST_BENEFIT: self._cost_benefit_method,
            DecisionMethod.RISK_ANALYSIS: self._risk_analysis_method,
            DecisionMethod.MULTI_CRITERIA: self._multi_criteria_method,
            DecisionMethod.INTUITIVE: self._intuitive_method
        }
        
        # Configurações padrão
        self.default_confidence_threshold = config.agency.decision_confidence_threshold
        self.risk_tolerance = config.agency.risk_tolerance
        
        # Estatísticas
        self.stats = {
            'decisions_made': 0,
            'average_confidence': 0.0,
            'method_usage': {method.value: 0 for method in DecisionMethod},
            'successful_decisions': 0
        }
        
        self.logger.info("DecisionMaker inicializado")
    
    async def make_decision(
        self,
        question: str,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        decision_type: DecisionType = DecisionType.MULTIPLE_CHOICE,
        preferred_method: Optional[DecisionMethod] = None,
        context: Dict[str, Any] = None
    ) -> DecisionResult:
        """
        Toma uma decisão estruturada.
        
        Args:
            question: Pergunta ou problema de decisão
            options: Opções disponíveis
            criteria: Critérios de avaliação
            decision_type: Tipo de decisão
            preferred_method: Método preferido (opcional)
            context: Contexto adicional
            
        Returns:
            Resultado da decisão
        """
        try:
            decision_id = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            self.logger.info(f"Tomando decisão: {question}")
            
            # Selecionar método de decisão
            method = preferred_method or self._select_best_method(
                decision_type, options, criteria, context or {}
            )
            
            # Validar entrada
            self._validate_decision_input(options, criteria)
            
            # Aplicar método de decisão
            result = await self.decision_methods[method](
                decision_id, question, options, criteria, context or {}
            )
            
            # Armazenar decisão
            self.decisions[decision_id] = result
            
            # Atualizar estatísticas
            self._update_statistics(result)
            
            self.logger.info(f"Decisão tomada: {result.recommended_option} (confiança: {result.confidence_level:.2f})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao tomar decisão: {e}")
            raise
    
    def _select_best_method(
        self,
        decision_type: DecisionType,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        context: Dict[str, Any]
    ) -> DecisionMethod:
        """Seleciona o melhor método de decisão"""
        
        # Mapeamento de tipos para métodos recomendados
        type_method_mapping = {
            DecisionType.BINARY: DecisionMethod.PROS_CONS,
            DecisionType.MULTIPLE_CHOICE: DecisionMethod.WEIGHTED_SCORING,
            DecisionType.RANKING: DecisionMethod.MULTI_CRITERIA,
            DecisionType.RESOURCE_ALLOCATION: DecisionMethod.COST_BENEFIT,
            DecisionType.STRATEGIC: DecisionMethod.DECISION_TREE,
            DecisionType.OPERATIONAL: DecisionMethod.WEIGHTED_SCORING
        }
        
        # Método baseado no tipo
        base_method = type_method_mapping.get(decision_type, DecisionMethod.WEIGHTED_SCORING)
        
        # Ajustar baseado no contexto
        if context.get('high_risk', False):
            return DecisionMethod.RISK_ANALYSIS
        
        if context.get('complex_criteria', False) and len(criteria) > 5:
            return DecisionMethod.MULTI_CRITERIA
        
        if len(options) == 2:
            return DecisionMethod.PROS_CONS
        
        if context.get('cost_sensitive', False):
            return DecisionMethod.COST_BENEFIT
        
        return base_method
    
    def _validate_decision_input(self, options: List[DecisionOption], criteria: List[DecisionCriterion]):
        """Valida entrada da decisão"""
        if not options:
            raise ValueError("Pelo menos uma opção deve ser fornecida")
        
        if not criteria:
            raise ValueError("Pelo menos um critério deve ser fornecido")
        
        # Verificar se todas as opções têm scores para todos os critérios
        criterion_names = {c.name for c in criteria}
        for option in options:
            option_criteria = set(option.scores.keys())
            missing_criteria = criterion_names - option_criteria
            if missing_criteria:
                self.logger.warning(f"Opção {option.name} não tem scores para: {missing_criteria}")
        
        # Verificar se pesos dos critérios somam aproximadamente 1.0
        total_weight = sum(c.weight for c in criteria)
        if abs(total_weight - 1.0) > 0.1:
            self.logger.warning(f"Pesos dos critérios somam {total_weight:.2f}, não 1.0")
    
    # Métodos de decisão específicos
    
    async def _weighted_scoring_method(
        self,
        decision_id: str,
        question: str,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        context: Dict[str, Any]
    ) -> DecisionResult:
        """Método de pontuação ponderada"""
        try:
            scores = {}
            criteria_analysis = {}
            
            # Calcular score ponderado para cada opção
            for option in options:
                total_score = 0.0
                option_analysis = {}
                
                for criterion in criteria:
                    if criterion.name in option.scores:
                        raw_score = option.scores[criterion.name]
                        
                        # Normalizar score (assumindo escala 0-10)
                        normalized_score = raw_score / 10.0
                        
                        # Inverter se critério é de custo (menor é melhor)
                        if not criterion.is_benefit:
                            normalized_score = 1.0 - normalized_score
                        
                        weighted_score = normalized_score * criterion.weight
                        total_score += weighted_score
                        
                        option_analysis[criterion.name] = {
                            'raw_score': raw_score,
                            'normalized_score': normalized_score,
                            'weighted_score': weighted_score,
                            'weight': criterion.weight
                        }
                
                scores[option.id] = total_score
                criteria_analysis[option.id] = option_analysis
            
            # Encontrar melhor opção
            best_option_id = max(scores.items(), key=lambda x: x[1])[0]
            best_score = scores[best_option_id]
            
            # Calcular confiança baseada na diferença entre as melhores opções
            sorted_scores = sorted(scores.values(), reverse=True)
            if len(sorted_scores) > 1:
                score_gap = sorted_scores[0] - sorted_scores[1]
                confidence = min(0.95, 0.5 + score_gap)
            else:
                confidence = 0.8
            
            # Criar lista de alternativas
            alternatives = [
                (option_id, score) for option_id, score in 
                sorted(scores.items(), key=lambda x: x[1], reverse=True)[1:]
            ]
            
            # Gerar raciocínio
            best_option = next(o for o in options if o.id == best_option_id)
            reasoning = self._generate_weighted_scoring_reasoning(
                best_option, criteria, criteria_analysis[best_option_id], best_score
            )
            
            return DecisionResult(
                decision_id=decision_id,
                recommended_option=best_option_id,
                confidence_level=confidence,
                reasoning=reasoning,
                alternative_options=alternatives,
                method_used=DecisionMethod.WEIGHTED_SCORING,
                criteria_analysis=criteria_analysis,
                risk_assessment={},
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro no método de pontuação ponderada: {e}")
            raise
    
    async def _pros_cons_method(
        self,
        decision_id: str,
        question: str,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        context: Dict[str, Any]
    ) -> DecisionResult:
        """Método de análise de prós e contras"""
        try:
            analysis = {}
            
            for option in options:
                pros = option.pros or []
                cons = option.cons or []
                
                # Calcular score baseado em prós e contras
                pros_score = len(pros) * 0.6  # Peso para prós
                cons_score = len(cons) * 0.4   # Peso para contras
                
                # Score final (prós positivos, contras negativos)
                final_score = pros_score - cons_score
                
                analysis[option.id] = {
                    'pros': pros,
                    'cons': cons,
                    'pros_count': len(pros),
                    'cons_count': len(cons),
                    'score': final_score
                }
            
            # Encontrar melhor opção
            best_option_id = max(analysis.items(), key=lambda x: x[1]['score'])[0]
            best_analysis = analysis[best_option_id]
            
            # Calcular confiança
            scores = [a['score'] for a in analysis.values()]
            if len(scores) > 1:
                best_score = max(scores)
                second_best = sorted(scores, reverse=True)[1]
                confidence = min(0.9, 0.6 + (best_score - second_best) * 0.1)
            else:
                confidence = 0.7
            
            # Alternativas
            alternatives = [
                (option_id, data['score']) for option_id, data in 
                sorted(analysis.items(), key=lambda x: x[1]['score'], reverse=True)[1:]
            ]
            
            # Raciocínio
            best_option = next(o for o in options if o.id == best_option_id)
            reasoning = f"""Análise de prós e contras para '{best_option.name}':

Prós ({best_analysis['pros_count']}):
{chr(10).join(f"• {pro}" for pro in best_analysis['pros'])}

Contras ({best_analysis['cons_count']}):
{chr(10).join(f"• {con}" for con in best_analysis['cons'])}

Esta opção apresenta o melhor balanço entre vantagens e desvantagens."""
            
            return DecisionResult(
                decision_id=decision_id,
                recommended_option=best_option_id,
                confidence_level=confidence,
                reasoning=reasoning,
                alternative_options=alternatives,
                method_used=DecisionMethod.PROS_CONS,
                criteria_analysis=analysis,
                risk_assessment={},
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro no método de prós e contras: {e}")
            raise
    
    async def _cost_benefit_method(
        self,
        decision_id: str,
        question: str,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        context: Dict[str, Any]
    ) -> DecisionResult:
        """Método de análise custo-benefício"""
        try:
            analysis = {}
            
            for option in options:
                cost = option.estimated_cost
                benefit = option.estimated_benefit
                
                # Calcular ROI (Return on Investment)
                if cost > 0:
                    roi = (benefit - cost) / cost
                else:
                    roi = benefit  # Se custo é zero, ROI é o benefício total
                
                # Calcular razão benefício/custo
                if cost > 0:
                    benefit_cost_ratio = benefit / cost
                else:
                    benefit_cost_ratio = float('inf') if benefit > 0 else 0
                
                # Score final considerando ROI e razão B/C
                score = roi * 0.6 + benefit_cost_ratio * 0.4
                
                analysis[option.id] = {
                    'cost': cost,
                    'benefit': benefit,
                    'roi': roi,
                    'benefit_cost_ratio': benefit_cost_ratio,
                    'score': score
                }
            
            # Encontrar melhor opção
            best_option_id = max(analysis.items(), key=lambda x: x[1]['score'])[0]
            best_analysis = analysis[best_option_id]
            
            # Calcular confiança baseada na diferença de ROI
            rois = [a['roi'] for a in analysis.values()]
            if len(rois) > 1:
                best_roi = max(rois)
                second_best_roi = sorted(rois, reverse=True)[1]
                confidence = min(0.95, 0.7 + abs(best_roi - second_best_roi) * 0.1)
            else:
                confidence = 0.8
            
            # Alternativas
            alternatives = [
                (option_id, data['score']) for option_id, data in 
                sorted(analysis.items(), key=lambda x: x[1]['score'], reverse=True)[1:]
            ]
            
            # Raciocínio
            best_option = next(o for o in options if o.id == best_option_id)
            reasoning = f"""Análise custo-benefício para '{best_option.name}':

• Custo estimado: {best_analysis['cost']:.2f}
• Benefício estimado: {best_analysis['benefit']:.2f}
• ROI: {best_analysis['roi']:.2%}
• Razão Benefício/Custo: {best_analysis['benefit_cost_ratio']:.2f}

Esta opção oferece o melhor retorno sobre o investimento."""
            
            return DecisionResult(
                decision_id=decision_id,
                recommended_option=best_option_id,
                confidence_level=confidence,
                reasoning=reasoning,
                alternative_options=alternatives,
                method_used=DecisionMethod.COST_BENEFIT,
                criteria_analysis=analysis,
                risk_assessment={},
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro no método custo-benefício: {e}")
            raise
    
    async def _risk_analysis_method(
        self,
        decision_id: str,
        question: str,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        context: Dict[str, Any]
    ) -> DecisionResult:
        """Método de análise de risco"""
        try:
            analysis = {}
            
            for option in options:
                risk_level = option.risk_level
                benefit = option.estimated_benefit
                implementation_difficulty = option.implementation_difficulty
                
                # Calcular score ajustado pelo risco
                risk_penalty = risk_level * 0.3
                difficulty_penalty = implementation_difficulty * 0.2
                
                # Score considerando benefício menos penalidades
                adjusted_score = benefit - (risk_penalty + difficulty_penalty)
                
                # Calcular razão risco-benefício
                if risk_level > 0:
                    risk_benefit_ratio = benefit / risk_level
                else:
                    risk_benefit_ratio = benefit * 10  # Baixo risco = alta razão
                
                analysis[option.id] = {
                    'risk_level': risk_level,
                    'benefit': benefit,
                    'implementation_difficulty': implementation_difficulty,
                    'risk_penalty': risk_penalty,
                    'difficulty_penalty': difficulty_penalty,
                    'adjusted_score': adjusted_score,
                    'risk_benefit_ratio': risk_benefit_ratio
                }
            
            # Encontrar melhor opção considerando tolerância ao risco
            if self.risk_tolerance == 'low':
                # Priorizar baixo risco
                best_option_id = min(analysis.items(), key=lambda x: x[1]['risk_level'])[0]
            elif self.risk_tolerance == 'high':
                # Priorizar alto benefício
                best_option_id = max(analysis.items(), key=lambda x: x[1]['benefit'])[0]
            else:  # medium
                # Balancear risco e benefício
                best_option_id = max(analysis.items(), key=lambda x: x[1]['adjusted_score'])[0]
            
            best_analysis = analysis[best_option_id]
            
            # Calcular confiança baseada no risco
            confidence = max(0.5, 1.0 - best_analysis['risk_level'])
            
            # Alternativas
            alternatives = [
                (option_id, data['adjusted_score']) for option_id, data in 
                sorted(analysis.items(), key=lambda x: x[1]['adjusted_score'], reverse=True)
                if option_id != best_option_id
            ]
            
            # Raciocínio
            best_option = next(o for o in options if o.id == best_option_id)
            reasoning = f"""Análise de risco para '{best_option.name}':

• Nível de risco: {best_analysis['risk_level']:.2%}
• Benefício esperado: {best_analysis['benefit']:.2f}
• Dificuldade de implementação: {best_analysis['implementation_difficulty']:.2%}
• Score ajustado pelo risco: {best_analysis['adjusted_score']:.2f}
• Razão risco-benefício: {best_analysis['risk_benefit_ratio']:.2f}

Esta opção oferece o melhor equilíbrio entre risco e benefício considerando a tolerância ao risco configurada ({self.risk_tolerance})."""
            
            # Avaliação de risco detalhada
            risk_assessment = {
                'overall_risk': best_analysis['risk_level'],
                'risk_tolerance': self.risk_tolerance,
                'risk_factors': [
                    f"Risco inerente: {best_analysis['risk_level']:.2%}",
                    f"Dificuldade de implementação: {best_analysis['implementation_difficulty']:.2%}"
                ],
                'mitigation_suggestions': [
                    "Monitorar indicadores de risco durante implementação",
                    "Desenvolver planos de contingência",
                    "Revisar decisão se condições mudarem significativamente"
                ]
            }
            
            return DecisionResult(
                decision_id=decision_id,
                recommended_option=best_option_id,
                confidence_level=confidence,
                reasoning=reasoning,
                alternative_options=alternatives,
                method_used=DecisionMethod.RISK_ANALYSIS,
                criteria_analysis=analysis,
                risk_assessment=risk_assessment,
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro no método de análise de risco: {e}")
            raise
    
    async def _multi_criteria_method(
        self,
        decision_id: str,
        question: str,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        context: Dict[str, Any]
    ) -> DecisionResult:
        """Método de análise multi-critério (TOPSIS simplificado)"""
        try:
            # Implementação simplificada do TOPSIS
            # 1. Normalizar matriz de decisão
            normalized_matrix = self._normalize_decision_matrix(options, criteria)
            
            # 2. Aplicar pesos
            weighted_matrix = self._apply_weights(normalized_matrix, criteria)
            
            # 3. Identificar soluções ideais
            ideal_positive, ideal_negative = self._identify_ideal_solutions(weighted_matrix, criteria)
            
            # 4. Calcular distâncias
            distances = self._calculate_distances(weighted_matrix, ideal_positive, ideal_negative)
            
            # 5. Calcular scores TOPSIS
            topsis_scores = {}
            for option_id, (dist_pos, dist_neg) in distances.items():
                if dist_pos + dist_neg > 0:
                    score = dist_neg / (dist_pos + dist_neg)
                else:
                    score = 0.5
                topsis_scores[option_id] = score
            
            # Encontrar melhor opção
            best_option_id = max(topsis_scores.items(), key=lambda x: x[1])[0]
            best_score = topsis_scores[best_option_id]
            
            # Calcular confiança
            scores = list(topsis_scores.values())
            if len(scores) > 1:
                score_std = math.sqrt(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))
                confidence = min(0.95, 0.6 + (1 - score_std))
            else:
                confidence = 0.8
            
            # Alternativas
            alternatives = [
                (option_id, score) for option_id, score in 
                sorted(topsis_scores.items(), key=lambda x: x[1], reverse=True)[1:]
            ]
            
            # Raciocínio
            best_option = next(o for o in options if o.id == best_option_id)
            reasoning = f"""Análise multi-critério (TOPSIS) para '{best_option.name}':

• Score TOPSIS: {best_score:.3f}
• Posição relativa às soluções ideais: {best_score:.1%}

Esta opção está mais próxima da solução ideal positiva considerando todos os critérios simultaneamente."""
            
            return DecisionResult(
                decision_id=decision_id,
                recommended_option=best_option_id,
                confidence_level=confidence,
                reasoning=reasoning,
                alternative_options=alternatives,
                method_used=DecisionMethod.MULTI_CRITERIA,
                criteria_analysis={
                    'topsis_scores': topsis_scores,
                    'ideal_positive': ideal_positive,
                    'ideal_negative': ideal_negative
                },
                risk_assessment={},
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro no método multi-critério: {e}")
            raise
    
    async def _decision_tree_method(
        self,
        decision_id: str,
        question: str,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        context: Dict[str, Any]
    ) -> DecisionResult:
        """Método de árvore de decisão (simplificado)"""
        try:
            # Implementação simplificada - usar critério mais importante como raiz
            most_important_criterion = max(criteria, key=lambda c: c.weight)
            
            analysis = {}
            
            for option in options:
                # Score baseado no critério mais importante
                primary_score = option.scores.get(most_important_criterion.name, 0)
                
                # Ajustar por outros critérios
                secondary_score = 0
                for criterion in criteria:
                    if criterion.name != most_important_criterion.name:
                        score = option.scores.get(criterion.name, 0)
                        secondary_score += score * criterion.weight
                
                # Score final
                final_score = primary_score * most_important_criterion.weight + secondary_score
                
                analysis[option.id] = {
                    'primary_criterion': most_important_criterion.name,
                    'primary_score': primary_score,
                    'secondary_score': secondary_score,
                    'final_score': final_score
                }
            
            # Encontrar melhor opção
            best_option_id = max(analysis.items(), key=lambda x: x[1]['final_score'])[0]
            best_analysis = analysis[best_option_id]
            
            # Confiança baseada na diferença de scores
            scores = [a['final_score'] for a in analysis.values()]
            if len(scores) > 1:
                best_score = max(scores)
                second_best = sorted(scores, reverse=True)[1]
                confidence = min(0.9, 0.6 + (best_score - second_best) / 10)
            else:
                confidence = 0.75
            
            # Alternativas
            alternatives = [
                (option_id, data['final_score']) for option_id, data in 
                sorted(analysis.items(), key=lambda x: x[1]['final_score'], reverse=True)[1:]
            ]
            
            # Raciocínio
            best_option = next(o for o in options if o.id == best_option_id)
            reasoning = f"""Análise por árvore de decisão para '{best_option.name}':

Critério principal: {most_important_criterion.name} (peso: {most_important_criterion.weight:.1%})
• Score no critério principal: {best_analysis['primary_score']:.1f}
• Score em critérios secundários: {best_analysis['secondary_score']:.1f}
• Score final: {best_analysis['final_score']:.1f}

Esta opção se destaca principalmente no critério mais importante da decisão."""
            
            return DecisionResult(
                decision_id=decision_id,
                recommended_option=best_option_id,
                confidence_level=confidence,
                reasoning=reasoning,
                alternative_options=alternatives,
                method_used=DecisionMethod.DECISION_TREE,
                criteria_analysis=analysis,
                risk_assessment={},
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro no método de árvore de decisão: {e}")
            raise
    
    async def _intuitive_method(
        self,
        decision_id: str,
        question: str,
        options: List[DecisionOption],
        criteria: List[DecisionCriterion],
        context: Dict[str, Any]
    ) -> DecisionResult:
        """Método intuitivo (heurísticas simples)"""
        try:
            analysis = {}
            
            for option in options:
                # Heurísticas simples
                scores = list(option.scores.values())
                
                # Score médio
                avg_score = sum(scores) / len(scores) if scores else 0
                
                # Penalizar por alto risco
                risk_penalty = option.risk_level * 2
                
                # Bonificar por baixa dificuldade
                ease_bonus = (1 - option.implementation_difficulty) * 1
                
                # Score intuitivo
                intuitive_score = avg_score - risk_penalty + ease_bonus
                
                analysis[option.id] = {
                    'average_score': avg_score,
                    'risk_penalty': risk_penalty,
                    'ease_bonus': ease_bonus,
                    'intuitive_score': intuitive_score
                }
            
            # Encontrar melhor opção
            best_option_id = max(analysis.items(), key=lambda x: x[1]['intuitive_score'])[0]
            best_analysis = analysis[best_option_id]
            
            # Confiança moderada para método intuitivo
            confidence = 0.65
            
            # Alternativas
            alternatives = [
                (option_id, data['intuitive_score']) for option_id, data in 
                sorted(analysis.items(), key=lambda x: x[1]['intuitive_score'], reverse=True)[1:]
            ]
            
            # Raciocínio
            best_option = next(o for o in options if o.id == best_option_id)
            reasoning = f"""Análise intuitiva para '{best_option.name}':

• Score médio nos critérios: {best_analysis['average_score']:.1f}
• Penalidade por risco: -{best_analysis['risk_penalty']:.1f}
• Bônus por facilidade: +{best_analysis['ease_bonus']:.1f}
• Score intuitivo final: {best_analysis['intuitive_score']:.1f}

Esta opção "sente-se" como a melhor escolha considerando simplicidade e praticidade."""
            
            return DecisionResult(
                decision_id=decision_id,
                recommended_option=best_option_id,
                confidence_level=confidence,
                reasoning=reasoning,
                alternative_options=alternatives,
                method_used=DecisionMethod.INTUITIVE,
                criteria_analysis=analysis,
                risk_assessment={},
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro no método intuitivo: {e}")
            raise
    
    # Métodos auxiliares para TOPSIS
    
    def _normalize_decision_matrix(self, options: List[DecisionOption], criteria: List[DecisionCriterion]) -> Dict[str, Dict[str, float]]:
        """Normaliza matriz de decisão"""
        normalized = {}
        
        # Calcular normas para cada critério
        norms = {}
        for criterion in criteria:
            values = [option.scores.get(criterion.name, 0) for option in options]
            norm = math.sqrt(sum(v**2 for v in values))
            norms[criterion.name] = norm if norm > 0 else 1
        
        # Normalizar valores
        for option in options:
            normalized[option.id] = {}
            for criterion in criteria:
                raw_value = option.scores.get(criterion.name, 0)
                normalized[option.id][criterion.name] = raw_value / norms[criterion.name]
        
        return normalized
    
    def _apply_weights(self, normalized_matrix: Dict[str, Dict[str, float]], criteria: List[DecisionCriterion]) -> Dict[str, Dict[str, float]]:
        """Aplica pesos à matriz normalizada"""
        weighted = {}
        
        for option_id, scores in normalized_matrix.items():
            weighted[option_id] = {}
            for criterion in criteria:
                weighted[option_id][criterion.name] = scores[criterion.name] * criterion.weight
        
        return weighted
    
    def _identify_ideal_solutions(self, weighted_matrix: Dict[str, Dict[str, float]], criteria: List[DecisionCriterion]) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Identifica soluções ideais positiva e negativa"""
        ideal_positive = {}
        ideal_negative = {}
        
        for criterion in criteria:
            values = [scores[criterion.name] for scores in weighted_matrix.values()]
            
            if criterion.is_benefit:
                ideal_positive[criterion.name] = max(values)
                ideal_negative[criterion.name] = min(values)
            else:
                ideal_positive[criterion.name] = min(values)
                ideal_negative[criterion.name] = max(values)
        
        return ideal_positive, ideal_negative
    
    def _calculate_distances(self, weighted_matrix: Dict[str, Dict[str, float]], ideal_positive: Dict[str, float], ideal_negative: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
        """Calcula distâncias às soluções ideais"""
        distances = {}
        
        for option_id, scores in weighted_matrix.items():
            # Distância à solução ideal positiva
            dist_pos = math.sqrt(sum(
                (scores[criterion] - ideal_positive[criterion])**2
                for criterion in scores.keys()
            ))
            
            # Distância à solução ideal negativa
            dist_neg = math.sqrt(sum(
                (scores[criterion] - ideal_negative[criterion])**2
                for criterion in scores.keys()
            ))
            
            distances[option_id] = (dist_pos, dist_neg)
        
        return distances
    
    def _generate_weighted_scoring_reasoning(self, option: DecisionOption, criteria: List[DecisionCriterion], analysis: Dict[str, Any], total_score: float) -> str:
        """Gera raciocínio para método de pontuação ponderada"""
        reasoning_parts = [f"Análise de pontuação ponderada para '{option.name}':"]
        reasoning_parts.append(f"Score total: {total_score:.3f}")
        reasoning_parts.append("")
        reasoning_parts.append("Detalhamento por critério:")
        
        for criterion in sorted(criteria, key=lambda c: c.weight, reverse=True):
            if criterion.name in analysis:
                crit_analysis = analysis[criterion.name]
                reasoning_parts.append(
                    f"• {criterion.name} (peso {criterion.weight:.1%}): "
                    f"{crit_analysis['raw_score']:.1f} → {crit_analysis['weighted_score']:.3f}"
                )
        
        reasoning_parts.append("")
        reasoning_parts.append("Esta opção apresenta o melhor desempenho ponderado considerando todos os critérios.")
        
        return "\n".join(reasoning_parts)
    
    def _update_statistics(self, result: DecisionResult):
        """Atualiza estatísticas do sistema"""
        self.stats['decisions_made'] += 1
        
        # Atualizar confiança média
        current_avg = self.stats['average_confidence']
        decision_count = self.stats['decisions_made']
        
        self.stats['average_confidence'] = (
            (current_avg * (decision_count - 1) + result.confidence_level) / decision_count
        )
        
        # Atualizar uso de métodos
        method_name = result.method_used.value
        self.stats['method_usage'][method_name] += 1
    
    # Métodos públicos
    
    def get_decision(self, decision_id: str) -> Optional[DecisionResult]:
        """Retorna decisão por ID"""
        return self.decisions.get(decision_id)
    
    def get_decision_summary(self, decision_id: str) -> Dict[str, Any]:
        """Retorna resumo de uma decisão"""
        if decision_id not in self.decisions:
            return {}
        
        decision = self.decisions[decision_id]
        
        return {
            'id': decision.decision_id,
            'recommended_option': decision.recommended_option,
            'confidence_level': decision.confidence_level,
            'method_used': decision.method_used.value,
            'alternatives_count': len(decision.alternative_options),
            'created_at': decision.created_at.isoformat(),
            'has_risk_assessment': bool(decision.risk_assessment)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de decisão"""
        return {
            **self.stats,
            'available_methods': [method.value for method in DecisionMethod],
            'decision_types': [dt.value for dt in DecisionType],
            'risk_tolerance': self.risk_tolerance
        }
    
    async def explain_decision(self, decision_id: str) -> str:
        """Explica uma decisão tomada"""
        if decision_id not in self.decisions:
            return "Decisão não encontrada."
        
        decision = self.decisions[decision_id]
        
        explanation = f"""Explicação da Decisão {decision_id}:

Método utilizado: {decision.method_used.value}
Opção recomendada: {decision.recommended_option}
Nível de confiança: {decision.confidence_level:.1%}

Raciocínio:
{decision.reasoning}

Alternativas consideradas:
"""
        
        for i, (option_id, score) in enumerate(decision.alternative_options[:3], 1):
            explanation += f"{i}. {option_id} (score: {score:.3f})\n"
        
        if decision.risk_assessment:
            explanation += f"\nAvaliação de risco:\n"
            explanation += f"Risco geral: {decision.risk_assessment.get('overall_risk', 'N/A')}\n"
        
        return explanation
