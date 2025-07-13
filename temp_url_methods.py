    def extract_from_url(self, url: str, output_dir: str = "citations") -> Optional[Dict]:
        """Extract citation from URL using trafilatura and newspaper3k."""
        try:
            print(f"🌐 Starting URL citation extraction...")
            
            # Clean the URL
            cleaned_url = clean_url(url)
            print(f"🔧 URL cleaned: {cleaned_url}")
            
            citation_info = {}
            
            # Step 1: Try trafilatura
            print("🔍 Step 1: Extracting with trafilatura...")
            downloaded = trafilatura.fetch_url(cleaned_url)
            if downloaded:
                metadata = trafilatura.extract_metadata(downloaded)
                if metadata:
                    if metadata.title:
                        citation_info['title'] = metadata.title
                    if metadata.author:
                        citation_info['author'] = format_author_name(metadata.author)
                    if metadata.date:
                        citation_info['date'] = metadata.date
                    if metadata.sitename:
                        citation_info['publisher'] = metadata.sitename
                    
                    print(f"📝 Trafilatura extraction: {len(citation_info)} fields found")
                    logging.info(f"Trafilatura metadata: {citation_info}")
            
            # Step 2: Fallback to newspaper3k if needed
            if not citation_info.get('title') or not citation_info.get('author'):
                print("🔍 Step 2: Trying newspaper3k as fallback...")
                try:
                    article = Article(cleaned_url)
                    article.download()
                    article.parse()
                    
                    if not citation_info.get('title') and article.title:
                        citation_info['title'] = article.title
                        print(f"📝 Newspaper3k extracted title: {article.title}")
                    
                    if not citation_info.get('author') and article.authors:
                        authors_str = ', '.join(article.authors)
                        citation_info['author'] = format_author_name(authors_str)
                        print(f"👥 Newspaper3k extracted authors: {article.authors}")
                    
                    if not citation_info.get('date') and article.publish_date:
                        citation_info['date'] = article.publish_date.strftime('%Y-%m-%d')
                        print(f"📅 Newspaper3k extracted date: {article.publish_date}")
                        
                except Exception as e:
                    print(f"⚠️ Newspaper3k failed: {e}")
                    logging.error(f"Newspaper3k error: {e}")
            
            # Step 3: Fallback to HTML meta tags if still missing required fields
            if not citation_info.get('title') or not citation_info.get('author'):
                print("🔍 Step 3: Trying HTML meta tags as fallback...")
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    
                    response = requests.get(cleaned_url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract title from meta tags or page title
                    if not citation_info.get('title'):
                        title_tag = soup.find('title')
                        if title_tag:
                            citation_info['title'] = title_tag.get_text().strip()
                            print(f"📝 HTML title extracted: {citation_info['title']}")
                    
                    # Extract author from meta tags
                    if not citation_info.get('author'):
                        author_meta = soup.find('meta', attrs={'name': 'author'})
                        if author_meta and author_meta.get('content'):
                            citation_info['author'] = format_author_name(author_meta.get('content'))
                            print(f"👤 HTML meta author extracted: {citation_info['author']}")
                    
                except Exception as e:
                    print(f"⚠️ HTML meta extraction failed: {e}")
                    logging.error(f"HTML meta extraction error: {e}")
            
            # Step 4: Extract publisher from domain if not provided
            if not citation_info.get('publisher'):
                domain_publisher = extract_publisher_from_domain(cleaned_url)
                if domain_publisher:
                    citation_info['publisher'] = domain_publisher
                    print(f"🏢 Publisher derived from domain: {domain_publisher}")
            
            # Step 5: Check if we have required fields
            if not citation_info.get('title'):
                print("❌ Error: Could not extract title from URL")
                return None
            
            if not citation_info.get('author'):
                print("❌ Error: Could not extract author from URL")
                return None
            
            # Add URL and access date
            citation_info['url'] = url  # Original URL
            citation_info['date_accessed'] = datetime.now().strftime('%Y-%m-%d')
            
            # Step 6: Save output
            print("💾 Step 6: Saving citation files...")
            save_citation(citation_info, url, output_dir)
            print("✅ URL citation extraction completed successfully!")
            return citation_info
            
        except Exception as e:
            logging.error(f"Error extracting citation from URL: {e}")
            print(f"❌ Error extracting citation from URL: {e}")
            return None
