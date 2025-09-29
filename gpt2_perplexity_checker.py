#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import torch
import numpy as np
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import warnings
warnings.filterwarnings("ignore")

class GPT2PerplexityChecker:
    def __init__(self, model_name="gpt2"):
        """
        初始化GPT-2困惑度检查器
        可选模型:
        - "gpt2" (117M parameters, 快速)
        - "gpt2-medium" (345M parameters, 中等)
        - "gpt2-large" (774M parameters, 大但准确)
        - "gpt2-xl" (1.5B parameters, 最大最准确但很慢)
        """
        print(f"🔄 正在加载GPT-2模型: {model_name}")
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"📱 使用设备: {self.device}")
        
        try:
            # 加载tokenizer和模型
            print("   📥 加载tokenizer...")
            self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            
            print("   📥 加载模型...")
            self.model = GPT2LMHeadModel.from_pretrained(model_name)
            
            # 设置pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 移动到设备并设置评估模式
            self.model.to(self.device)
            self.model.eval()
            
            print(f"✅ GPT-2模型加载成功")
            print(f"   模型参数: {sum(p.numel() for p in self.model.parameters()):,}")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            print("💡 请确保安装了必要的依赖:")
            print("   pip install transformers torch")
            print("   如果使用GPU: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            raise
    
    def load_sentences(self, filename="selected_sentences_analyzer.json"):
        """加载句子数据"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    sentences = json.load(f)
                print(f"📁 加载了 {len(sentences)} 个句子")
                return sentences
            except Exception as e:
                print(f"❌ 加载句子文件失败: {e}")
                return []
        else:
            print(f"❌ 未找到文件: {filename}")
            return []
    
    def calculate_perplexity_single(self, text, max_length=512):
        """计算单个句子的困惑度"""
        try:
            # 编码文本
            encodings = self.tokenizer(
                text, 
                return_tensors='pt', 
                truncation=True, 
                max_length=max_length,
                padding=False
            )
            
            input_ids = encodings.input_ids.to(self.device)
            
            # 确保输入不为空
            if input_ids.size(1) == 0:
                return float('inf'), float('inf')
            
            # 计算困惑度
            with torch.no_grad():
                # 使用input_ids作为labels来计算loss
                outputs = self.model(input_ids, labels=input_ids)
                loss = outputs.loss
                
                # 困惑度 = exp(loss)
                perplexity = torch.exp(loss).item()
                
                # 如果loss是nan或inf，返回无穷大
                if not torch.isfinite(loss):
                    return float('inf'), float('inf')
            
            return perplexity, loss.item()
            
        except Exception as e:
            print(f"❌ 计算困惑度失败: {text[:50]}... - {e}")
            return float('inf'), float('inf')
    
    def calculate_perplexity_sliding_window(self, text, stride=512, max_length=1024):
        """使用滑动窗口计算长句子的困惑度"""
        try:
            encodings = self.tokenizer(text, return_tensors='pt')
            input_ids = encodings.input_ids.to(self.device)
            
            seq_len = input_ids.size(1)
            
            # 如果句子短于max_length，直接计算
            if seq_len <= max_length:
                return self.calculate_perplexity_single(text, max_length)
            
            # 使用滑动窗口
            nlls = []
            prev_end_loc = 0
            
            for begin_loc in range(0, seq_len, stride):
                end_loc = min(begin_loc + max_length, seq_len)
                trg_len = end_loc - prev_end_loc
                
                input_ids_window = input_ids[:, begin_loc:end_loc]
                target_ids = input_ids_window.clone()
                target_ids[:, :-trg_len] = -100
                
                with torch.no_grad():
                    outputs = self.model(input_ids_window, labels=target_ids)
                    neg_log_likelihood = outputs.loss * trg_len
                
                nlls.append(neg_log_likelihood)
                prev_end_loc = end_loc
                
                if end_loc == seq_len:
                    break
            
            # 计算平均困惑度
            total_nll = torch.stack(nlls).sum()
            perplexity = torch.exp(total_nll / seq_len).item()
            avg_loss = (total_nll / seq_len).item()
            
            return perplexity, avg_loss
            
        except Exception as e:
            print(f"❌ 滑动窗口计算失败: {text[:50]}... - {e}")
            return float('inf'), float('inf')
    
    def batch_calculate_perplexity(self, sentences, batch_size=4, use_sliding_window=False):
        """批量计算困惑度"""
        results = []
        total = len(sentences)
        
        print(f"\n🔄 开始使用GPT-2计算 {total} 个句子的困惑度...")
        print(f"📊 批处理大小: {batch_size}")
        print(f"🪟 滑动窗口: {'启用' if use_sliding_window else '禁用'}")
        
        for i in range(0, total, batch_size):
            batch = sentences[i:i+batch_size]
            batch_results = []
            
            for j, sentence in enumerate(batch):
                current_idx = i + j + 1
                print(f"⏳ 处理中 ({current_idx}/{total}): {sentence[:60]}{'...' if len(sentence) > 60 else ''}")
                
                # 选择计算方法
                if use_sliding_window:
                    perplexity, loss = self.calculate_perplexity_sliding_window(sentence)
                else:
                    perplexity, loss = self.calculate_perplexity_single(sentence)
                
                # 计算一些额外的统计信息
                tokens = self.tokenizer.encode(sentence)
                token_count = len(tokens)
                word_count = len(sentence.split())
                
                batch_results.append({
                    'index': current_idx,
                    'sentence': sentence,
                    'perplexity': perplexity,
                    'loss': loss,
                    'token_count': token_count,
                    'word_count': word_count,
                    'avg_perplexity_per_token': perplexity / token_count if token_count > 0 else float('inf')
                })
            
            results.extend(batch_results)
            
            # 显示进度和当前批次统计
            progress = (i + len(batch)) / total * 100
            batch_perplexities = [r['perplexity'] for r in batch_results if r['perplexity'] != float('inf')]
            if batch_perplexities:
                batch_avg = sum(batch_perplexities) / len(batch_perplexities)
                print(f"📈 进度: {progress:.1f}% ({i + len(batch)}/{total}) | 当前批次平均困惑度: {batch_avg:.2f}")
            else:
                print(f"📈 进度: {progress:.1f}% ({i + len(batch)}/{total})")
            
            # 清理GPU缓存（如果使用GPU）
            if self.device.type == 'cuda':
                torch.cuda.empty_cache()
        
        return results
    
    def analyze_results(self, results):
        """分析GPT-2困惑度结果"""
        if not results:
            print("❌ 没有结果可分析")
            return
        
        # 过滤掉无效结果
        valid_results = [r for r in results if r['perplexity'] != float('inf')]
        
        if not valid_results:
            print("❌ 没有有效的困惑度计算结果")
            return
        
        perplexities = [r['perplexity'] for r in valid_results]
        
        print("\n" + "=" * 90)
        print(f"📊 GPT-2 困惑度分析结果 (模型: {self.model_name})")
        print("=" * 90)
        
        # 统计信息
        print(f"\n📈 统计摘要:")
        print(f"   总句子数: {len(results)}")
        print(f"   有效计算: {len(valid_results)}")
        print(f"   平均困惑度: {np.mean(perplexities):.2f}")
        print(f"   中位数困惑度: {np.median(perplexities):.2f}")
        print(f"   最低困惑度: {np.min(perplexities):.2f}")
        print(f"   最高困惑度: {np.max(perplexities):.2f}")
        print(f"   标准差: {np.std(perplexities):.2f}")
        
        # 困惑度分布
        low_perp = sum(1 for p in perplexities if p < 20)
        med_perp = sum(1 for p in perplexities if 20 <= p < 50)
        high_perp = sum(1 for p in perplexities if p >= 50)
        
        print(f"\n📊 困惑度分布:")
        print(f"   低困惑度 (<20): {low_perp} 句 ({low_perp/len(valid_results)*100:.1f}%)")
        print(f"   中困惑度 (20-50): {med_perp} 句 ({med_perp/len(valid_results)*100:.1f}%)")
        print(f"   高困惑度 (≥50): {high_perp} 句 ({high_perp/len(valid_results)*100:.1f}%)")
        
        # 按困惑度排序
        sorted_results = sorted(valid_results, key=lambda x: x['perplexity'])
        
        # 显示最自然的句子（低困惑度）
        print(f"\n🌟 最自然的句子 (低困惑度):")
        print("-" * 80)
        for i, result in enumerate(sorted_results[:15], 1):
            print(f"{i:2d}. 困惑度: {result['perplexity']:7.2f} | 词数: {result['word_count']:2d} | {result['sentence']}")
        
        # 显示最不自然的句子（高困惑度）
        print(f"\n⚠️  最不自然的句子 (高困惑度):")
        print("-" * 80)
        for i, result in enumerate(sorted_results[-15:], 1):
            print(f"{i:2d}. 困惑度: {result['perplexity']:7.2f} | 词数: {result['word_count']:2d} | {result['sentence']}")
        
        return sorted_results
    
    def save_results(self, results, filename="gpt2_perplexity_report.json"):
        """保存结果到文件"""
        try:
            # 保存JSON格式
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 保存可读文本格式
            txt_filename = filename.replace('.json', '.txt')
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write("GPT-2 句子困惑度分析报告\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"模型: {self.model_name}\n")
                f.write(f"总句子数: {len(results)}\n")
                
                # 统计信息
                valid_results = [r for r in results if r['perplexity'] != float('inf')]
                if valid_results:
                    perplexities = [r['perplexity'] for r in valid_results]
                    f.write(f"有效计算: {len(valid_results)}\n")
                    f.write(f"平均困惑度: {np.mean(perplexities):.2f}\n")
                    f.write(f"中位数困惑度: {np.median(perplexities):.2f}\n")
                    f.write(f"最低困惑度: {np.min(perplexities):.2f}\n")
                    f.write(f"最高困惑度: {np.max(perplexities):.2f}\n")
                f.write("\n")
                
                # 按困惑度排序的详细结果
                sorted_results = sorted([r for r in results if r['perplexity'] != float('inf')], 
                                      key=lambda x: x['perplexity'])
                
                f.write("所有句子的困惑度 (按困惑度排序):\n")
                f.write("-" * 60 + "\n")
                
                for result in sorted_results:
                    f.write(f"\n困惑度: {result['perplexity']:7.2f} | 词数: {result['word_count']:2d} | Token数: {result['token_count']:3d}\n")
                    f.write(f"句子: {result['sentence']}\n")
            
            print(f"✅ 结果已保存到:")
            print(f"   📄 {filename} (JSON格式)")
            print(f"   📄 {txt_filename} (文本格式)")
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")

def main():
    print("🎯 GPT-2 句子困惑度检查器")
    print("=" * 60)
    
    # 选择模型
    models = {
        "1": "gpt2",
        "2": "gpt2-medium", 
        "3": "gpt2-large",
        "4": "gpt2-xl"
    }
    
    print("📚 可用的GPT-2模型:")
    print("   1. GPT-2 (117M参数, 快速)")
    print("   2. GPT-2 Medium (345M参数, 中等)")
    print("   3. GPT-2 Large (774M参数, 准确但慢)")
    print("   4. GPT-2 XL (1.5B参数, 最准确但很慢)")
    
    choice = input("\n选择模型 (1-4, 默认1): ").strip() or "1"
    model_name = models.get(choice, "gpt2")
    
    try:
        # 初始化检查器
        checker = GPT2PerplexityChecker(model_name)
        
        # 加载句子
        sentences = checker.load_sentences()
        if not sentences:
            return
        
        # 设置参数
        batch_size = int(input(f"\n批处理大小 (默认2): ").strip() or "2")
        
        use_sliding_window = input("是否使用滑动窗口处理长句子? (y/N): ").strip().lower() in ['y', 'yes']
        
        # 批量计算困惑度
        results = checker.batch_calculate_perplexity(
            sentences, 
            batch_size=batch_size,
            use_sliding_window=use_sliding_window
        )
        
        # 分析结果
        sorted_results = checker.analyze_results(results)
        
        # 保存结果
        if sorted_results:
            save_choice = input("\n💾 是否保存结果? (y/N): ").strip().lower()
            if save_choice in ['y', 'yes']:
                filename = f"gpt2_{model_name.replace('-', '_')}_perplexity_report.json"
                checker.save_results(results, filename)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("💡 可能的解决方案:")
        print("   1. 确保网络连接正常（首次运行需要下载模型）")
        print("   2. 尝试使用更小的模型")
        print("   3. 减小批处理大小")
        print("   4. 确保有足够的内存/显存")

if __name__ == "__main__":
    main()


