import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface StoryParagraph {
  text: string;
  image_url?: string;
  audio_url?: string;
  image_style?: string;
}

const StoryEdit: React.FC = () => {
  const navigate = useNavigate();
  const [paragraphs, setParagraphs] = useState<StoryParagraph[]>([]);

  const handleTextChange = (index: number, newText: string) => {
    setParagraphs(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], text: newText };
      return updated;
    });
  };

  const handleContinue = () => {
    navigate('/story/edit/nodes');
  };

  return (
    <div className="container max-w-4xl mx-auto py-8">
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Edit Your Story</h1>
          <Button onClick={handleContinue} className="bg-gradient-to-r from-primary to-purple-600">
            Continue to Node Editor
          </Button>
        </div>

        <ScrollArea className="h-[calc(100vh-12rem)] pr-4">
          <div className="space-y-6">
            {paragraphs.map((paragraph, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-lg">Paragraph {index + 1}</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    value={paragraph.text}
                    onChange={(e) => handleTextChange(index, e.target.value)}
                    className="min-h-[150px]"
                    placeholder="Enter your paragraph text..."
                  />
                </CardContent>
                <CardFooter className="justify-end space-x-2">
                  {paragraph.image_url && (
                    <Button variant="outline" size="sm">
                      View Image
                    </Button>
                  )}
                  {paragraph.audio_url && (
                    <Button variant="outline" size="sm">
                      Play Audio
                    </Button>
                  )}
                </CardFooter>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
};

export default StoryEdit;
