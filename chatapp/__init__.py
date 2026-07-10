"""Chat application with a 4-layer cognitive memory architecture.

Layers
------
1. Working Context    -> relational tables (conversations, messages)
2. Persistent Memory  -> relational table (user_profiles, JSONB document)
3. Compacted History  -> vector collection "compacted_history"
4. Indexed Files      -> vector collection "indexed_files"
"""
