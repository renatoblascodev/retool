---
name: frontend-react-mobile
description: 'Especialista em React 19, TypeScript e React Native para web builder e aplicativos mobile. Use para componentes do editor visual, runtime client-side, Zustand, TanStack Query, @dnd-kit, performance, testes frontend e apps móveis com Expo.'
argument-hint: 'Descreva a feature web ou mobile a implementar, revisar ou otimizar.'
user-invocable: true
---

# Frontend React + Mobile

## Quando Usar

- Implementar telas e componentes React
- Criar widgets do canvas e painel de propriedades
- Trabalhar com Zustand, TanStack Query e runtime client-side
- Construir ou revisar app mobile com React Native e Expo
- Diagnosticar performance, re-render e organização de estado

## Objetivo

Entregar frontend e mobile tipados, performáticos e testáveis, com separação clara entre editor, preview e runtime.

## Padrões Obrigatórios

- TypeScript estrito
- Server state em TanStack Query
- UI/editor state em Zustand apenas quando necessário
- Componentes pequenos, com responsabilidade única
- Virtualização para listas grandes
- Testes para comportamento crítico

## Procedimento

1. Identifique se a feature pertence a editor, runtime, preview, auth ou mobile.
2. Defina o módulo e os tipos públicos primeiro.
3. Escolha o estado correto: local, query cache ou store global.
4. Implemente componente e hook sem misturar responsabilidades.
5. Adicione tratamento de loading, error e empty state.
6. Cubra o comportamento principal com teste.

## Decisões Padrão

- Web: React 19, Vite, Material UI, @dnd-kit, react-grid-layout
- Mobile: Expo, Expo Router, NativeWind, Reanimated
- Nunca usar `any` sem justificativa explícita
- Nunca usar store global para dados que pertencem ao servidor

## Guardrails

- Não misturar estado do builder com estado do viewer
- Não bloquear execução esperando API final: usar mocks/MSW quando necessário
- Não otimizar cedo demais sem evidência real

## Saídas Típicas

- componente React completo
- hook de integração com API
- store do editor
- tela mobile
- revisão de performance e arquitetura frontend