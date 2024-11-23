import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { motion } from 'framer-motion';
import { Progress } from '@/components/ui/progress';

const formSchema = z.object({
  prompt: z.string().min(10, 'Story prompt must be at least 10 characters long'),
  genre: z.string().min(1, 'Please select a genre'),
  mood: z.string().min(1, 'Please select a mood'),
  target_audience: z.string().min(1, 'Please select a target audience'),
  paragraphs: z.number().min(1).max(20).default(5),
});

type FormValues = z.infer<typeof formSchema>;

const genres = ['Fantasy', 'Science Fiction', 'Mystery', 'Romance', 'Adventure', 'Horror', 'Historical Fiction'];
const moods = ['Happy', 'Mysterious', 'Adventure', 'Dark', 'Romantic', 'Humorous', 'Suspenseful'];
const audiences = ['Children', 'Young Adult', 'Adult'];

const StoryGeneration: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      paragraphs: 5,
    },
  });

  const [generationStep, setGenerationStep] = useState<string>('');
  const [progress, setProgress] = useState(0);

  const onSubmit = async (values: FormValues) => {
    setIsLoading(true);
    setProgress(0);
    setGenerationStep('Initializing');
    try {
      const formData = new FormData();
      Object.entries(values).forEach(([key, value]) => {
        formData.append(key, value.toString());
      });

      const response = await fetch('/generate_story', {
        method: 'POST',
        body: formData,
      });

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Failed to get reader');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;

          try {
            const data = JSON.parse(line.trim());
            if (data.type === 'progress') {
              setProgress(data.progress);
              setGenerationStep(data.step);
            } else if (data.type === 'complete') {
              // Use navigate instead of window.location for proper SPA navigation
              navigate(data.redirect);
              return;
            } else if (data.type === 'error') {
              throw new Error(data.message);
            }
          } catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            // Only log the error and continue, don't break the stream
            continue;
          }
        }
      }
    } catch (error) {
      console.error('Error generating story:', error);
      form.setError('root', {
        message: error instanceof Error ? error.message : 'An unexpected error occurred',
      });
    } finally {
      setIsLoading(false);
      setProgress(0);
      setGenerationStep('');
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] bg-gradient-to-b from-background to-primary/5">
      <div className="container max-w-2xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-8"
        >
          <div className="text-center space-y-2">
            <h1 className="font-display text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600">
              Create Your Story
            </h1>
            <p className="font-serif text-lg text-muted-foreground">
              Let AI help you craft your next masterpiece
            </p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="prompt"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Story Prompt</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Enter your story idea..."
                        className="h-32 resize-none"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Describe your story idea in detail to get better results
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="genre"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Genre</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a genre" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {genres.map((genre) => (
                            <SelectItem key={genre} value={genre.toLowerCase()}>
                              {genre}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="mood"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mood</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a mood" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {moods.map((mood) => (
                            <SelectItem key={mood} value={mood.toLowerCase()}>
                              {mood}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="target_audience"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Target Audience</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select target audience" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {audiences.map((audience) => (
                            <SelectItem key={audience} value={audience.toLowerCase()}>
                              {audience}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="paragraphs"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Number of Paragraphs</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={1}
                          max={20}
                          {...field}
                          onChange={event => field.onChange(parseInt(event.target.value))}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="space-y-4">
                {(isLoading || progress > 0) && (
                  <div className="space-y-2">
                    <Progress value={progress} className="w-full" />
                    <p className="text-sm text-center text-muted-foreground">
                      {generationStep}
                    </p>
                  </div>
                )}
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-purple-600 hover:to-primary"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                      <span>Generating Story...</span>
                    </div>
                  ) : (
                    'Generate Story'
                  )}
                </Button>
              </div>

              {form.formState.errors.root && (
                <div className="text-red-500 text-center mt-2">
                  {form.formState.errors.root.message}
                </div>
              )}
            </form>
          </Form>
        </motion.div>
      </div>
    </div>
  );
};

export default StoryGeneration;
