"""
Cache Statistics and Management Tool

Usage:
    python manage_cache.py stats     # View cache statistics
    python manage_cache.py clear     # Clear all caches
    python manage_cache.py warmup    # Warmup cache with common queries
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.cache import MultiLevelCacheManager
import json


def show_stats():
    """Display cache statistics"""
    print("\n" + "="*80)
    print("MULTI-LEVEL CACHE STATISTICS")
    print("="*80)
    
    try:
        cache_manager = MultiLevelCacheManager()
        stats = cache_manager.get_all_stats()
        
        print(f"\n📊 Combined Hit Rate: {stats.get('combined_hit_rate', 'N/A')}")
        print(f"📦 Total Entries: {stats.get('total_entries', 0)}")
        
        for level in stats.get('levels', []):
            print(f"\n{'─'*80}")
            print(f"  {level.get('level', 'Unknown')} - {level.get('name', 'Unknown')}")
            print(f"{'─'*80}")
            print(f"  Entries:      {level.get('size', 0):,} / {level.get('max_entries', 0):,}")
            
            if 'ttl' in level:
                print(f"  TTL:          {level['ttl']}s")
            
            if 'similarity_threshold' in level:
                print(f"  Threshold:    {level['similarity_threshold']}")
            
            if 'keyspace_hits' in level:
                hits = level['keyspace_hits']
                misses = level['keyspace_misses']
                total = hits + misses
                hit_rate = (hits / total * 100) if total > 0 else 0
                print(f"  Hits:         {hits:,}")
                print(f"  Misses:       {misses:,}")
                print(f"  Hit Rate:     {hit_rate:.1f}%")
            
            if 'hit_rate' in level:
                print(f"  Hit Rate:     {level['hit_rate']}")
            
            if 'topics' in level:
                topics = level['topics']
                if topics:
                    print(f"  Topics:       {len(topics)}")
                    for topic, count in list(topics.items())[:5]:
                        print(f"    - {topic}: {count} entries")
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Error retrieving stats: {e}")
        import traceback
        traceback.print_exc()


def clear_all():
    """Clear all cache levels"""
    print("\n⚠️  WARNING: This will clear all cache levels!")
    confirm = input("Are you sure? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    try:
        cache_manager = MultiLevelCacheManager()
        results = cache_manager.clear_all()
        
        print("\n✅ Cache cleared:")
        for level, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {level}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")


def warmup_cache():
    """Warmup cache with common queries"""
    print("\n🔥 Warming up cache with common queries...")
    
    common_queries = [
        # Data Structures
        "What is a binary tree?",
        "Explain hash tables",
        "What is a linked list?",
        "How do stacks work?",
        "Explain graph data structure",
        
        # Algorithms
        "What is binary search?",
        "Explain quicksort algorithm",
        "What is dynamic programming?",
        "Explain BFS algorithm",
        "What is Dijkstra's algorithm?",
        
        # Time Complexity
        "What is Big O notation?",
        "Explain time complexity",
        "What is O(n log n)?",
        
        # Programming Concepts
        "What is recursion?",
        "Explain object-oriented programming",
        "What are design patterns?",
    ]
    
    try:
        from ai_engine.agents import teacher_agent
        from ai_engine.state import AgentState
        
        cached_count = 0
        
        for query in common_queries:
            print(f"  Processing: {query[:50]}...")
            
            state = AgentState(
                query=query,
                user_id="warmup_bot",
                complexity_score=50
            )
            
            result = teacher_agent(state)
            
            if result.get("response"):
                cached_count += 1
        
        print(f"\n✅ Warmed up {cached_count}/{len(common_queries)} queries")
        print("   Run 'python manage_cache.py stats' to see results\n")
        
    except Exception as e:
        print(f"❌ Error during warmup: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == 'stats':
        show_stats()
    elif command == 'clear':
        clear_all()
    elif command == 'warmup':
        warmup_cache()
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
