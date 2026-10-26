Attribute VB_Name = "ThisDocument"
' Macro de TREINO extraida do documento "pedido_frete_outubro.docm" (ficticio).
' Imita o padrao de um anexo malicioso, mas o comando final so escreve uma mensagem.
Sub AutoOpen()
    Atualizar
End Sub

Sub Document_Open()
    Atualizar
End Sub

Sub Atualizar()
    Dim p As String
    p = "pow" & "ershell -nop -w hidden -enc "
    p = p & "VwByAGkAdABlAC0ASABvAHMAdAAgACcAVAByAGUAaQBuAGEAbQBlAG4AdABvACAAQgBlACAAUwBhAGYAZQA6ACAAZQBzAHQAYQAgAG0AYQBjAHIAbwAgAHQAZQBuAHQAYQByAGkAYQAgAGUAeABlAGMAdQB0AGEAcgAgAFAAbwB3AGUAcgBTAGgAZQBsAGwAJwA="
    Shell p, vbHide
End Sub
